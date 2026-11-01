"""Validate the frozen A0 export's internal consistency, not external raw files."""

import json
import math
from collections import Counter

MODEL_SHA = "d49e0ade33734a0723d82198a4774ddb9745c004d45feb4a8db1aec528b8af77"
SCRIPT_SHA = "b266c60aa40b3a6751896a65c62355dabd841c6c80902517fe34cd4bcf64fb0a"
RAW_SHA = "4e1dcee2983a90d84daf8d3074ab1bf2f7b6246db9cb3d8646e70325f30d3858"
HF_SHA = "b78433b33b7d9f9da964852e5b88987f43a0ee52552cbb6ab83aeeabd8c27e75"
PREFIX = "model.paligemma_with_expert."
TIED_SOURCE = PREFIX + "paligemma.lm_head.weight"
TIED_ALIAS = PREFIX + "paligemma.model.language_model.embed_tokens.weight"


def require(condition, message):
    if not condition:
        raise ValueError(f"A0 loading audit: {message}")


def check_loading(directory):
    data = json.loads((directory / "checkpoint_loading.json").read_text())
    identity = json.loads((directory / "checkpoint_identity.json").read_text())
    require(type(data.get("schema")) is int and data["schema"] == 1, "unsupported schema")
    require(data.get("source_report_sha256") == RAW_SHA, "changed/missing raw-report fingerprint")
    execution, report = data["execution"], data["report"]
    require(execution.get("script_sha256") == SCRIPT_SHA, "changed/missing instrumentation fingerprint")
    for field, count in {"exit_code": 0, "policy_instantiations": 1, "policy_forwards": 0,
                         "simulated_episodes": 0, "weight_conversions": 0, "CPU_threads": 4,
                         "timeout_seconds": 600, "source_keys_used": 777}.items():
        require(type(execution.get(field)) is int and execution[field] == count, f"incorrect execution count: {field}")
    require(execution.get("GPU_use") is False and report.get("cpu_only") is True, "CPU-only scope changed")
    require(execution.get("model_state_entries_include_tied_aliases") is True, "missing tied-alias declaration")
    require(execution.get("configuration_overrides") == {"device": "cpu", "compile_model": False, "default_device": "cpu"},
            "unexpected configuration overrides")
    elapsed = execution.get("elapsed_seconds")
    require(type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 < elapsed <= 600, "invalid elapsed time")
    expected_inputs = {
        "${EMB_ROOT}/src/lerobot/src/lerobot/policies/pi0/modeling_pi0.py": MODEL_SHA,
        "${EMB_ROOT}/src/lerobot/src/lerobot/policies/pi0/configuration_pi0.py": "1c8a29acb69a8a6ad87be3e1a273a29089293779aa7e16f75efbde93d399d20d",
        "${EMB_ROOT}/ckpt/pi0_libero_base@98ac51b8_openpi/config.json": "2405b602e3b4f3fe8f5e2239e8fa74fad0e69650af2b0fdf8af1c17798669e90",
        "${EMB_ROOT}/ckpt/pi0_libero_base@98ac51b8/model.safetensors": HF_SHA,
    }
    require(report.get("input_sha256") == report.get("expected_input_sha256") == expected_inputs, "input fingerprints disagree")
    require(identity["hf_expected_lfs_sha256"] == identity["file_identity"]["hf_weight_sha256"] == HF_SHA,
            "HF identity/loading fingerprints disagree")
    require(report.get("status") == "PARAMETERS_MATCH", "expected the recorded complete match")
    for field in ("model_entries", "checked_entries"):
        require(type(report.get(field)) is int and report[field] == 778, f"incorrect {field}")
    for field in ("unchecked_entries", "missing", "unknown_checkpoint_keys", "mismatched", "nonfinite"):
        require(report.get(field) == [], f"missing/nonempty error list: {field}")
    buffers = [f"model.{stage}.buffer_{field}.{stat}" for stage, field in
               [("normalize_inputs", "observation_state"), ("normalize_targets", "action"), ("unnormalize_outputs", "action")]
               for stat in ("mean", "std")]
    require(sorted(report.get("legacy_buffer_keys", [])) == sorted(buffers), "legacy buffer warning inventory changed")
    require(isinstance(report.get("loader_output"), str) and all(key in report["loader_output"] for key in buffers),
            "missing recorded legacy-buffer warnings")

    reference = {row["key"]: row for row in identity["array_comparison"]["tensors"]}
    require(len(reference) == len(identity["array_comparison"]["tensors"]) == 775, "invalid reference tensor inventory")
    for key, width in [(TIED_SOURCE, 2048), (PREFIX + "gemma_expert.lm_head.weight", 1024)]:
        reference[key] = {"shape": [257152, width], "hf_dtype": "BF16"}
    entries = report.get("parameters")
    require(isinstance(entries, list) and len(entries) == 778, "incomplete per-entry inventory")
    names = [row["parameter"] for row in entries]
    require(len(set(names)) == len(names) and set(names) == set(reference) | {TIED_ALIAS}, "duplicate/missing/unknown model entries")
    for row in entries:
        name = row["parameter"]
        source = TIED_SOURCE if name == TIED_ALIAS else name
        require(row.get("source_key") == source, f"undeclared source mapping: {name}")
        require(row.get("shape") == reference[source]["shape"], f"shape mismatch: {name}")
        require(row.get("source_dtype") == {"F32": "torch.float32", "BF16": "torch.bfloat16"}[reference[source]["hf_dtype"]],
                f"source dtype mismatch: {name}")
        require(row.get("actual_dtype") in {"torch.float32", "torch.bfloat16"}, f"unknown target dtype: {name}")
        for field in ("different_elements_after_target_cast", "nonfinite_actual_elements", "nonfinite_expected_elements"):
            require(type(row.get(field)) is int and row[field] == 0, f"nonzero/invalid {field}: {name}")
    require(len({row["source_key"] for row in entries}) == execution["source_keys_used"], "source-key count mismatch")
    require(Counter(row["actual_dtype"] for row in entries) == {"torch.float32": 523, "torch.bfloat16": 255},
            "target dtype totals changed")
    tied = [row for row in entries if row["source_key"] == TIED_SOURCE]
    require(len(tied) == 2 and tied[0]["actual_dtype"] == tied[1]["actual_dtype"], "tied alias dtype mismatch")
