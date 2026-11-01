"""CPU-only parameter identity audit against the pinned OpenPI array mapping.

Requires NumPy and TensorStore (available in the recorded OpenPI environment).
No model, Torch, JAX or simulator is imported. Reports metadata, never weights.
A difference exits1; incomplete matching exits2; complete mapped matching exits0.
"""

import argparse
import ast
import hashlib
import json
import mmap
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

CONVERTER_SHA = "62980fda1a1b1a09167d413232a2a9295db8370e52b58a70cfba52ef5d88c440"


def compare_array(array, stored, kind):
    """Compare after the declared storage cast; do not confuse BF16 with F16."""
    if array.dtype != np.float32 or array.size == 0:
        raise ValueError("Need nonempty float32 native parameters")
    different, maximum = 0, 0.0
    for start in range(0, array.size, 1_000_000):
        x, raw = array.flat[start:start + 1_000_000], stored[start:start + 1_000_000]
        if not np.isfinite(x).all():
            raise ValueError("Non-finite native parameter")
        if kind == "BF16":
            bits = x.view(np.uint32)
            rounded = ((bits + np.uint32(0x7FFF) + ((bits >> 16) & 1)) >> 16).astype(np.uint16)
            y = (raw.astype(np.uint32) << 16).view(np.float32)
            expected = (rounded.astype(np.uint32) << 16).view(np.float32)
        else:
            expected = x.astype({"F32": "<f4", "F16": "<f2"}[kind]).astype(np.float32)
            y = raw.astype(np.float32)
        different += int(np.count_nonzero(expected != y))
        if not np.isfinite(y).all():
            raise ValueError("Non-finite stored parameter")
        maximum = max(maximum, float(np.max(np.abs(expected - y))))
    return different, maximum


def reference_functions(converter):
    source = converter.read_bytes()
    if hashlib.sha256(source).hexdigest() != CONVERTER_SHA:
        raise ValueError("Converter differs from the reviewed pinned source")
    names = {"slice_paligemma_state_dict", "slice_gemma_state_dict"}
    functions = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name in names]
    if len(functions) != 2:
        raise ValueError("Missing pinned array conversion functions")
    # These wrappers only change array containers, not the reference arithmetic.
    namespace = {"np": np, "torch": SimpleNamespace(Tensor=np.ndarray, from_numpy=lambda x: x)}
    exec(compile(ast.Module(body=functions, type_ignores=[]), "<pinned-array-mapping>", "exec"), namespace)
    return namespace


def mapped_parameters(params, converter):
    functions = reference_functions(converter)
    available = int(next(s.split()[1] for s in Path("/proc/meminfo").read_text().splitlines()
                         if s.startswith("MemAvailable:"))) * 1024
    if available <= 40 * 1024**3:
        raise ValueError("Need more than40 GiB available RAM for this bounded CPU-only check")
    import tensorstore as ts
    spec = {"driver": "ocdbt", "base": "file://" + str(params.resolve()) + "/"}
    metadata = json.loads((params / "_METADATA").read_text())["tree_metadata"]
    pg, projections, nbytes = {}, {}, 0
    for entry in metadata.values():
        parts = [k["key"] for k in entry["key_metadata"]]
        if parts[0] != "params" or parts[-1] != "value":
            raise ValueError("Unexpected native parameter layout")
        store = ts.open({"driver": "zarr", "kvstore": spec, "path": ".".join(parts)}, read=True, write=False).result()
        if nbytes + store.size * 4 >= 16 * 1024**3:
            raise ValueError("Native float32 arrays exceed the16GiB audit bound")
        a = store.read().result().astype(np.float32)
        nbytes += a.nbytes
        if parts[1] == "PaliGemma":
            pg["/".join(parts[2:-1])] = a
        else:
            name, suffix = parts[1:-1]
            projections[name + (".weight" if suffix == "kernel" else ".bias")] = a.T if suffix == "kernel" else a
    cfg = SimpleNamespace(vision_config=SimpleNamespace(hidden_size=1152, num_hidden_layers=27),
                          text_config=SimpleNamespace(hidden_size=2048, num_hidden_layers=18, num_attention_heads=8, head_dim=256))
    paligemma, expert = functions["slice_paligemma_state_dict"](pg, cfg)
    cfg = SimpleNamespace(width=1024, depth=18, num_heads=8, head_dim=256)
    gemma = functions["slice_gemma_state_dict"](expert, cfg, num_expert=1, checkpoint_dir=str(params.parent), pi05=False)
    return {"model." + k: v for k, v in {**paligemma, **gemma, **projections}.items()}, len(metadata), nbytes


def compare_file(mapped, checkpoint):
    if not mapped:
        raise ValueError("No mapped parameters to compare")
    rows, missing = [], []
    with checkpoint.open("rb") as f:
        size = struct.unpack("<Q", f.read(8))[0]
        header, offset = json.loads(f.read(size)), 8 + size
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            for key, a in sorted(mapped.items()):
                if key not in header:
                    missing.append(key)
                    continue
                meta = header[key]
                if list(a.shape) != meta["shape"]:
                    raise ValueError(f"Shape mismatch: {key}")
                kind = meta["dtype"]
                dtype = {"F32": "<f4", "BF16": "<u2", "F16": "<f2"}[kind]
                lo, hi = meta["data_offsets"]
                if hi - lo != a.size * np.dtype(dtype).itemsize:
                    raise ValueError(f"Invalid byte range: {key}")
                # Own the buffer so a validation traceback cannot keep an mmap
                # view alive and mask the original error with BufferError.
                stored = np.frombuffer(mm, dtype=dtype, count=a.size, offset=offset + lo).copy()
                try:
                    different, maximum = compare_array(a, stored, kind)
                finally:
                    del stored
                rows.append({"key": key, "shape": list(a.shape), "hf_dtype": kind, "elements": int(a.size),
                             "different_elements": different, "max_abs_after_declared_cast": maximum})
    extra = sorted(k for k in header if k != "__metadata__" and k not in mapped)
    different = sum(r["different_elements"] > 0 for r in rows)
    status = "DIFFERENT_UNDER_REFERENCE_MAPPING" if different else ("INCONCLUSIVE" if missing or extra else "MATCHED_MAPPED_PARAMETERS")
    return {"status": status, "mapped_tensors": len(mapped), "compared_tensors": len(rows), "missing_hf_keys": missing,
            "extra_hf_keys": extra, "exact_after_declared_cast": len(rows) - different, "different_tensors": different, "tensors": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("native_params", type=Path)
    parser.add_argument("hf_checkpoint", type=Path)
    parser.add_argument("converter", type=Path)
    parser.add_argument("--output", type=Path, help="Unused JSON filename; default prints the report")
    args = parser.parse_args(argv)
    try:
        if args.output is not None and (args.output.exists() or args.output.is_symlink()):
            raise FileExistsError(f"Output exists: {args.output}")
        mapped, arrays, nbytes = mapped_parameters(args.native_params, args.converter)
        report = compare_file(mapped, args.hf_checkpoint)
        report.update(converter_sha256=CONVERTER_SHA, cpu_only=True, native_parameter_arrays=arrays, native_float32_bytes=nbytes,
                      scope="Declared-dtype parameter identity under the pinned mapping; not functional equivalence or a failure mechanism")
        text = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if args.output is None:
            print(text, end="")
        else:
            with args.output.open("x") as output:
                output.write(text)
    except (OSError, ValueError, KeyError, TypeError, ImportError, struct.error) as error:
        print(f"Checkpoint identity: {error}", file=sys.stderr)
        return 2
    return {"DIFFERENT_UNDER_REFERENCE_MAPPING": 1, "INCONCLUSIVE": 2, "MATCHED_MAPPED_PARAMETERS": 0}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
