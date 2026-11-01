"""P1 staged runner: gates on evidence, never overwrites an existing run."""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(os.environ["EMB_ROOT"])
JOB = Path(__file__).resolve().parents[2]
CK = ROOT / "ckpt/pi0_libero_finetuned_v044@45dcc8fc"
PREFIX = os.environ.get("STATE_RUN_PREFIX", "statefb_20261031")
if not re.fullmatch(r"[A-Za-z0-9_-]+", PREFIX):
    raise ValueError("STATE_RUN_PREFIX must be a simple run identifier")
GROUPS = {"A": ("none", "live"), "B": ("all", "live"), "C": ("none", "freeze_initial"), "D": ("all", "freeze_initial")}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate(path, n):
    d = json.loads((path / "evidence.json").read_text())
    rows = d["episodes"]
    assert len(rows) == 10 * n
    assert {(r["task"], r["initial"]) for r in rows} == {(t, i) for t in range(10) for i in range(n)}
    info = json.loads((path / "out/eval_info.json").read_text())
    assert info["overall"]["n_episodes"] == 10 * n
    assert all(len(t["metrics"]["successes"]) == n for t in info["per_task"])
    traj = np.load(path / "traj.npz")
    assert int(traj["n"]) == len(rows)
    for i, row in enumerate(rows):
        states = np.load(path / row["state_file"])
        raw, norm, sent = states["raw"], states["normalized"], states["sent"]
        assert len(norm) == len(sent) == row["image_checks"] > 0
        assert row["masks"] == [True, True, False]
        assert np.isfinite(raw).all() and np.isfinite(norm).all() and np.isfinite(sent).all()
        assert norm.shape == sent.shape and norm.shape[1:] == (1, 32)
        assert raw.shape[1:] == (1, 8)
        steps = states["inference_steps"]
        assert np.array_equal(steps, np.arange(1, len(raw) + 1, 5))
        assert np.isfinite(traj[f"act_{i}"]).all() and len(traj[f"act_{i}"]) > 0
        if d["mode"] == "live":
            assert np.array_equal(sent, norm)
        else:
            assert np.array_equal(sent, np.repeat(sent[:1], len(sent), axis=0))
    assert any(r["state_changes"] for r in rows), "no real-state movement observed"
    return rows, info["overall"]


def cross(paths, n):
    validated = {g: validate(p, n) for g, p in paths.items()}
    baseline = {(r["task"], r["initial"]): (r["first_frame_hash"], r["eef0"], r["noise_seed"]) for r in validated["A"][0]}
    for rows, _ in validated.values():
        assert {(r["task"], r["initial"]): (r["first_frame_hash"], r["eef0"], r["noise_seed"]) for r in rows} == baseline
    print("GATE PASS", {g: v[1]["pc_success"] for g, v in validated.items()}, flush=True)


def run(stage, group, repeat, n):
    path = ROOT / "logs/eval" / f"{PREFIX}_{stage}_{group}"
    path.mkdir(exist_ok=False)
    black, mode = GROUPS[group]
    env = {**os.environ, "BLACKOUT": black, "STATE_FEEDBACK": mode, "STATE_REPEAT": str(repeat),
           "STATE_EVIDENCE": str(path / "evidence.json"), "TRAJ_OUT": str(path / "traj.npz"), "HF_HUB_OFFLINE": "1"}
    env.pop("POLICY_SERVER", None)
    args = [sys.executable, str(JOB / "scripts/eval/eval_state_feedback.py"), f"--policy.path={CK}",
            "--policy.device=cuda", "--policy.n_action_steps=5", "--env.type=libero", "--env.task=libero_spatial",
            "--env.observation_height=360", "--env.observation_width=360", "--env.max_parallel_tasks=1",
            "--eval.batch_size=1", f"--eval.n_episodes={n}", "--seed=1000", f"--output_dir={path / 'out'}"]
    (path / "invocation.json").write_text(json.dumps({"args": args, "blackout": black, "state_feedback": mode, "repeat": repeat}, indent=2))
    print(f"START {stage} {group}", flush=True)
    with (path / "stdout.log").open("w") as log:
        rc = subprocess.call(args, cwd=path, env=env, stdout=log, stderr=subprocess.STDOUT)
    (path / "exit_code").write_text(str(rc))
    if rc:
        raise RuntimeError(f"{stage} {group}: exit={rc}, see {path}/stdout.log")
    _, stats = validate(path, n)
    print(f"END {stage} {group} {stats}", flush=True)
    return path


def main():
    lock = JOB / "started.flag"
    with lock.open("x") as f:
        f.write("started\n")
    assert json.loads((CK / "config.json").read_text())["input_features"]["observation.state"]["shape"] == [8]
    pre = json.loads((CK / "policy_preprocessor.json").read_text())
    post = json.loads((CK / "policy_postprocessor.json").read_text())
    assert [x["registry_name"] for x in post["steps"]] == ["unnormalizer_processor", "device_processor"]
    manifest = {"checkpoint_files": {p.name: digest(p) for p in CK.iterdir() if p.suffix in {".json", ".safetensors"}},
                "scripts": {str(p.relative_to(JOB)): digest(p) for p in (JOB / "scripts").rglob("*.py")},
                "preprocessor": pre, "postprocessor": post}
    import mujoco
    import torch
    manifest.update(torch=torch.__version__, mujoco=mujoco.__version__, cudnn_deterministic=torch.backends.cudnn.deterministic,
                    deterministic_algorithms=torch.are_deterministic_algorithms_enabled())
    assert mujoco.__version__ == "3.3.2"
    (JOB / "manifest.json").write_text(json.dumps(manifest, indent=2))
    smoke = {g: run("smoke", g, 0, 1) for g in "ABCD"}
    cross(smoke, 1)
    (JOB / "smoke_pass.flag").write_text("all four conditions validated\n")
    for repeat, order in enumerate(("ABCD", "DCBA", "BDAC")):
        paths = {g: run(f"r{repeat}", g, repeat, 10) for g in order}
        cross(paths, 10)
        (JOB / f"r{repeat}_pass.flag").write_text("validated\n")
    (JOB / "done.flag").write_text("1200 formal + 40 smoke completed\n")


if __name__ == "__main__":
    main()
