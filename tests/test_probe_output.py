"""Exercise the real shell/probe exit path with a CPU-only fake evaluator."""

import os
import shlex
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from test_entry_scripts import ROOT

pytest_plugins = ["test_entry_scripts"]


@pytest.mark.parametrize("failure", ["none", "write", "evaluator", "empty"])
def test_probe_finalization_controls_shell_status(emb, fake_lerobot, failure):
    stub = Path(fake_lerobot)
    (stub / "numpy.py").unlink()  # Use NumPy for the archive, never a real policy/backend.
    (stub / "lerobot/scripts/lerobot_eval.py").write_text('''
import os
import sys
from pathlib import Path
preprocess_observation = rollout = None
def main():
    mode = os.environ["PROBE_TEST_FAILURE"]
    if mode != "empty":
        sys.modules["__main__"].episodes.append({
            "eef": [[1., 2., 3.]], "grip": [[0., 0.]], "act": [[0.] * 7], "h0": "fixture"})
    if mode == "write":
        Path(os.environ["TRAJ_OUT"]).mkdir()
    if mode == "evaluator":
        raise SystemExit(23)
    return 0
''')
    (emb / "bin/python").write_text(f'#!/bin/bash\nexec {shlex.quote(sys.executable)} "$@"\n')
    r = subprocess.run(["bash", str(ROOT / "scripts/eval/run_libero.sh"), "probe", "1", "/fixture", "1"],
                       cwd=ROOT, capture_output=True, text=True, timeout=15,
                       env={**os.environ, "EMB_ROOT": str(emb), "WRAP": "probe", "BLACKOUT": "none",
                            "PYTHONPATH": fake_lerobot, "PROBE_TEST_FAILURE": failure})
    output = emb / "logs/eval/probe"
    log = (output / "stdout.log").read_text()
    if failure == "none":
        assert r.returncode == 0 and log.splitlines()[-1] == "exit=0"
    else:
        assert r.returncode != 0 and log.splitlines()[-1] != "exit=0"
    if failure in {"none", "evaluator"}:
        with np.load(output / "traj.npz") as archive:
            assert archive["n"] == 1
            assert archive["act_0"].shape == (1, 7)
            assert archive["h0"].tolist() == ["fixture"]
    if failure == "evaluator":
        assert r.returncode == 23
    if failure == "write":
        assert (output / "traj.npz").is_dir()  # Failed evidence is retained.


def test_probe_does_not_replace_an_existing_trajectory(tmp_path, fake_lerobot):
    stub = Path(fake_lerobot)
    (stub / "numpy.py").unlink()
    (stub / "lerobot/scripts/lerobot_eval.py").write_text('''
import sys
preprocess_observation = rollout = None
def main():
    sys.modules["__main__"].episodes.append({"eef": [], "grip": [], "act": []})
    return 0
''')
    output = tmp_path / "keep.npz"
    output.write_bytes(b"existing evidence")
    r = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/eval/eval_probe.py")], capture_output=True, timeout=15,
                       env={**os.environ, "PYTHONPATH": fake_lerobot, "TRAJ_OUT": str(output), "BLACKOUT": "none"})
    assert r.returncode != 0
    assert output.read_bytes() == b"existing evidence"
