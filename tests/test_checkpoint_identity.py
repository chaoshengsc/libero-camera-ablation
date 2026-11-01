"""Small same-shape negative controls for the CPU parameter identity audit."""

import hashlib
import json
import struct

import numpy as np
import pytest
from check_checkpoint_identity import compare_file, main, reference_functions


def checkpoint(path, tensors):
    header, contents, offset = {}, [], 0
    for name, (kind, shape, value) in tensors.items():
        raw = value.tobytes()
        header[name] = {"dtype": kind, "shape": shape, "data_offsets": [offset, offset + len(raw)]}
        contents.append(raw)
        offset += len(raw)
    raw = json.dumps(header).encode()
    raw += b" " * ((-len(raw)) % 8)
    path.write_bytes(struct.pack("<Q", len(raw)) + raw + b"".join(contents))


def test_same_shape_parameter_change_is_a_mismatch(tmp_path):
    path = tmp_path / "weights.safetensors"
    a = np.array([1, 2, 3], dtype=np.float32)
    for b, status in [(a, "MATCHED_MAPPED_PARAMETERS"), (a + 0.125, "DIFFERENT_UNDER_REFERENCE_MAPPING")]:
        checkpoint(path, {"model.x": ("F32", [3], b)})
        result = compare_file({"model.x": a}, path)
        assert result["status"] == status


def test_declared_bfloat16_rounding_is_not_a_false_mismatch(tmp_path):
    path = tmp_path / "weights.safetensors"
    # Known BF16 encodings of1 and2; values strictly closer to those than neighbours.
    a = np.array([1.0001, 2.0001], dtype=np.float32)
    checkpoint(path, {"model.x": ("BF16", [2], np.array([0x3F80, 0x4000], dtype="<u2"))})
    assert compare_file({"model.x": a}, path)["status"] == "MATCHED_MAPPED_PARAMETERS"


def test_missing_or_extra_tensors_are_not_full_identity(tmp_path):
    path = tmp_path / "weights.safetensors"
    a = np.array([1], dtype=np.float32)
    checkpoint(path, {"model.x": ("F32", [1], a)})
    assert compare_file({"model.x": a, "model.missing": a}, path)["status"] == "INCONCLUSIVE"
    checkpoint(path, {"model.x": ("F32", [1], a), "model.extra": ("F32", [1], a)})
    assert compare_file({"model.x": a}, path)["status"] == "INCONCLUSIVE"
    with pytest.raises(ValueError, match="No mapped"):
        compare_file({}, path)


def test_changed_reference_code_is_rejected_before_execution(tmp_path):
    path = tmp_path / "not_the_converter.py"
    path.write_text("raise RuntimeError('must never execute')")
    with pytest.raises(ValueError, match="reviewed pinned"):
        reference_functions(path)


@pytest.mark.parametrize("bad_native,bad_stored", [(True, False), (False, True)])
def test_nonfinite_parameter_keeps_original_error_and_cli_code(tmp_path, monkeypatch, bad_native, bad_stored):
    path = tmp_path / "weights.safetensors"
    native = np.array([np.nan if bad_native else 1], dtype=np.float32)
    stored = np.array([np.inf if bad_stored else 1], dtype=np.float32)
    checkpoint(path, {"model.x": ("F32", [1], stored)})
    with pytest.raises(ValueError, match="Non-finite"):
        compare_file({"model.x": native}, path)
    monkeypatch.setattr("check_checkpoint_identity.mapped_parameters", lambda *a: ({"model.x": native}, 1, native.nbytes))
    assert main(["unused-native", str(path), "unused-converter"]) == 2


def test_existing_output_is_rejected_before_backend_loading(tmp_path, monkeypatch):
    path = tmp_path / "report.json"
    path.write_bytes(b"keep")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr("check_checkpoint_identity.mapped_parameters", lambda *a: pytest.fail("backend loaded"))
    assert main(["no-native", "no-hf", "no-converter", "--output", str(path)]) == 2
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_real_published_audit_is_a_negative_identity_check():
    from summarize_protocol_audit import AUDIT
    d = json.loads((AUDIT / "checkpoint_identity.json").read_text())
    comparison = d["array_comparison"]
    assert comparison["compared_tensors"] == comparison["different_tensors"] == 775
    assert comparison["exact_after_declared_cast"] == 0
    assert d["file_identity"]["hf_weight_sha256"] == d["hf_expected_lfs_sha256"]
    assert len(d["file_identity"]["native_listing_verified"]) == 19
