"""Cross-device command recipes must agree with frozen evidence and remain print-only."""

import importlib.util
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dashboard/data"
MANIFEST = json.loads((ROOT / "configs/camera_study_runs.json").read_text())
SPEC = importlib.util.spec_from_file_location("camera_study_commands", ROOT / "scripts/eval/camera_study_commands.py")
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def test_recorded_configuration_matches_public_provenance_and_pairing():
    records = {row["id"]: row for row in json.loads((DATA / "protocol_audit/provenance.json").read_text())["runs"]}
    common = MANIFEST["historical_common"]
    expected = {f"s500/{path.name}" for path in (DATA / "s500").iterdir() if path.is_dir()}
    assert {row["run_id"] for row in MANIFEST["runs"]} == expected
    assert len(expected) == 11
    for row in MANIFEST["runs"]:
        info = json.loads((ROOT / row["eval_file"]).read_text())
        tasks = sorted(info["per_task"], key=lambda task: task["task_id"])
        assert [task["task_id"] for task in tasks] == common["task_ids"]
        assert all(len(task["metrics"]["successes"]) == common["episodes_per_task"] for task in tasks)
        source = records[row["provenance_id"]]
        assert source["total_episodes"] == common["total_episodes"] == 500
        assert source["budget"] == [common["control_budget"]]
        settings = source["settings"]
        for key in ["seed", "chunk_size", "num_inference_steps", "observation_height", "batch_size"]:
            manifest_key = "entry_seed" if key == "seed" else key
            assert settings[key] == [str(common[manifest_key])]
        assert settings["n_action_steps"] == [str(MANIFEST["models"][row["model"]]["n_action_steps"])]
        assert "observation_width" not in settings and common["observation_width"] is None
        assert row["analysis_normal_run"] == f"s500/{row['model']}_none"
        hashes = json.loads((ROOT / row["first_frame_hash_file"]).read_text())
        baseline = json.loads((DATA / row["analysis_normal_run"] / "first_frame_hash.json").read_text())
        assert len(hashes) == 500 and hashes == baseline
    historical = MANIFEST["historical_references"][0]
    assert historical["is_s500_paired_arm"] is False
    assert len(historical["raw_runs"]) == historical["repeats"] == 5
    for run in historical["raw_runs"]:
        info = json.loads((DATA / run / "eval_info.json").read_text())
        assert sum(len(task["metrics"]["successes"]) for task in info["per_task"]) == 100


@pytest.mark.parametrize("model,mode,steps", [("pi0", "wrist", 5), ("pi05", "drop_wrist", 10)])
@pytest.mark.parametrize("smoke,episodes", [(True, 1), (False, 50)])
def test_printed_command_preserves_model_and_intervention_without_running(tmp_path, capsys, model, mode, steps, smoke, episodes):
    work = tmp_path / "working directory with spaces"
    args = ["--run", f"s500/{model}_{mode}", "--new-run-name", "new_01", "--emb-root", str(work)]
    if smoke:
        args.append("--smoke")
    before = list(tmp_path.iterdir())
    assert helper.main(args) == 0
    output = capsys.readouterr()
    command = shlex.split(output.out.strip())
    assert command[0] == "env" and f"EMB_ROOT={work}" in command
    assert "WRAP=probe" in command and f"BLACKOUT={mode}" in command
    start = command.index("new_01")
    assert command[start + 1] == str(episodes)
    assert command[start + 2] == str(work / "ckpt" / MANIFEST["models"][model]["local_checkpoint_dir"])
    assert f"--policy.n_action_steps={steps}" in command
    assert "--env.observation_width=360" in command and "--env.episode_length=280" in command
    assert "unverified" in output.err
    assert list(tmp_path.iterdir()) == before


@pytest.mark.parametrize("name", ["..", "../escape", "bad name", "bad;command"])
def test_invalid_new_run_names_do_not_print_a_command(tmp_path, capsys, name):
    assert helper.main(["--run", "s500/pi0_none", "--new-run-name", name, "--emb-root", str(tmp_path)]) == 1
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("kind", ["directory", "file", "dangling_symlink"])
def test_existing_output_is_retained_and_rejected(tmp_path, kind):
    output = tmp_path / "logs/eval/used"
    output.parent.mkdir(parents=True)
    if kind == "directory":
        output.mkdir()
    elif kind == "file":
        output.write_text("keep original")
    else:
        output.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError, match="already exists"):
        helper.build_command(MANIFEST, "s500/pi0_none", "used", tmp_path)
    assert output.is_symlink() if kind == "dangling_symlink" else output.exists()
    if kind == "file":
        assert output.read_text() == "keep original"


def test_printed_environment_cannot_inherit_openpi_bridge_or_delta_diagnostics(tmp_path):
    command = shlex.split(helper.build_command(MANIFEST, "s500/pi05_drop_wrist", "new_01", tmp_path))
    prefix = command[: command.index("bash")]
    probe = "import json,os; print(json.dumps([os.getenv(k) for k in ['POLICY_SERVER','OPENPI_AUTHKEY','DELTA_REF']]))"
    environment = dict(os.environ, POLICY_SERVER="dummy-inherited-server", OPENPI_AUTHKEY="dummy-key", DELTA_REF="step")
    result = subprocess.run([*prefix, sys.executable, "-c", probe], env=environment, capture_output=True, text=True, check=True, timeout=10)
    assert json.loads(result.stdout) == [None, None, "chunk"]
