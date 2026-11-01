"""Guard the legacy demonstration exporter without model or simulator execution."""

import importlib.util
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import numpy as np
import pytest

SOURCE = Path(__file__).resolve().parents[1] / "viewer/export_act.py"
spec = importlib.util.spec_from_file_location("export_act", SOURCE)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


@pytest.mark.parametrize("kind", ["directory", "file", "symlink", "dangling_symlink"])
def test_existing_output_is_rejected_before_backend(tmp_path, monkeypatch, kind):
    target = tmp_path / "output"
    old = tmp_path / "old"
    old.mkdir()
    (old / "keep").write_text("original")
    if kind == "directory":
        target.mkdir()
        (target / "keep").write_text("original")
    elif kind == "file":
        target.write_text("original")
    else:
        target.symlink_to(old if kind == "symlink" else tmp_path / "absent")
    monkeypatch.setattr(exporter, "export_demo", lambda *args: pytest.fail("backend was called"))
    with pytest.raises(FileExistsError):
        exporter.run(target, tmp_path / "checkpoint")
    assert (old / "keep").read_text() == "original"
    if kind == "directory":
        assert [p.name for p in target.iterdir()] == ["keep"]
    elif kind == "file":
        assert target.read_text() == "original"
    else:
        assert target.is_symlink()


def test_failed_export_and_retry_preserve_partial_artifacts(tmp_path, monkeypatch):
    target = tmp_path / "failed"

    def broken(output, checkpoint):
        (output / "scene.mjb").write_bytes(b"partial")
        raise RuntimeError("backend failed")

    monkeypatch.setattr(exporter, "export_demo", broken)
    with pytest.raises(RuntimeError, match="backend failed"):
        exporter.run(target, tmp_path / "checkpoint")
    assert not (target / "done.json").exists()
    before = {p.name: p.read_bytes() for p in target.iterdir()}
    assert "backend failed" in json.loads(before["failure.json"])["error"]
    with pytest.raises(FileExistsError):
        exporter.run(target, tmp_path / "checkpoint")
    assert before == {p.name: p.read_bytes() for p in target.iterdir()}


def test_concurrent_export_reserves_only_one_output(tmp_path, monkeypatch):
    entered, release = Event(), Event()
    calls = []

    def backend(output, checkpoint):
        calls.append(output)
        entered.set()
        assert release.wait(5)
        return {"trajectory": "demo.npz"}

    monkeypatch.setattr(exporter, "export_demo", backend)
    target = tmp_path / "concurrent"
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(exporter.run, target, tmp_path / "checkpoint")
        assert entered.wait(5)
        try:
            with pytest.raises(FileExistsError):
                exporter.run(target, tmp_path / "checkpoint")
        finally:
            release.set()
        first.result()
    assert calls == [target] and (target / "done.json").is_file()


@pytest.fixture
def backend(monkeypatch):
    state = {"success_seed": 1002, "seeds": [], "closed": False, "load_error": False, "nan": False, "close_error": False}
    qpos = np.zeros(3)
    phys = SimpleNamespace(model=SimpleNamespace(_model=object()), data=SimpleNamespace(qpos=qpos))

    class Environment:
        unwrapped = SimpleNamespace(_env=SimpleNamespace(physics=phys))

        def reset(self, seed):
            state["seeds"].append(seed)
            self.seed, self.steps = seed, 0
            qpos[:] = 0
            return {"state": {"position": qpos.copy()}}, {}

        def step(self, action):
            self.steps += 1
            qpos[:] = float("nan") if state["nan"] else self.steps
            return {"state": {"position": qpos.copy()}}, 0, self.steps == 2, False, {"is_success": self.seed == state["success_seed"]}

        def close(self):
            state["closed"] = True
            if state["close_error"]:
                raise RuntimeError("close failed")

    class Action:
        def __getitem__(self, index):
            return self

        def cpu(self):
            return self

        def numpy(self):
            return np.zeros(7)

    def config(path):
        if state["load_error"]:
            raise RuntimeError("load failed")
        return SimpleNamespace()

    policy = SimpleNamespace(eval=lambda: None, reset=lambda: None, select_action=lambda batch: Action())
    for name, module in {
        "gym_aloha": SimpleNamespace(),
        "gymnasium": SimpleNamespace(make=lambda *args, **kwargs: Environment()),
        "mujoco": SimpleNamespace(__version__="test-only", mj_saveModel=lambda model, path, extra: Path(path).write_bytes(b"scene")),
        "torch": SimpleNamespace(inference_mode=nullcontext),
        "lerobot.configs.policies": SimpleNamespace(PreTrainedConfig=SimpleNamespace(from_pretrained=config)),
        "lerobot.envs.configs": SimpleNamespace(AlohaEnv=lambda **kwargs: SimpleNamespace()),
        "lerobot.envs.utils": SimpleNamespace(preprocess_observation=lambda obs: obs),
        "lerobot.policies.factory": SimpleNamespace(make_policy=lambda *args, **kwargs: policy,
                                                    make_pre_post_processors=lambda *args, **kwargs: (lambda x: x, lambda x: x)),
    }.items():
        monkeypatch.setitem(sys.modules, name, module)
    return state


@pytest.mark.parametrize("successful", [True, False])
def test_original_demo_selection_is_recorded(tmp_path, backend, successful):
    if not successful:
        backend["success_seed"] = None
    target = tmp_path / "demo"
    result = exporter.run(target, tmp_path / "checkpoint")
    seed = 1002 if successful else 1009
    assert backend["seeds"] == list(range(1000, seed + 1)) and backend["closed"]
    assert result["selected_seed"] == seed and result["success"] == successful
    assert result["scope"] == "demonstration_only"
    assert len(result["attempts"]) == (3 if successful else 10)
    assert json.loads((target / "done.json").read_text()) == result
    with np.load(target / result["trajectory"]) as trajectory:
        assert trajectory["qpos"].shape == (3, 3)
        assert int(trajectory["seed"]) == seed and bool(trajectory["success"]) == successful
        assert float(trajectory["dt"]) == 1 / 50


@pytest.mark.parametrize("failure", ["load_error", "nan", "close_error"])
def test_backend_errors_close_environment_and_never_complete(tmp_path, backend, failure):
    backend[failure] = True
    target = tmp_path / "failed"
    with pytest.raises((RuntimeError, ValueError)):
        exporter.run(target, tmp_path / "checkpoint")
    assert backend["closed"] and (target / "failure.json").is_file()
    assert not (target / "done.json").exists()


def test_cli_help_missing_environment_and_import_have_no_model_side_effects(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "EMB_ROOT"}
    help_result = subprocess.run([sys.executable, str(SOURCE), "--help"], env=env, capture_output=True, text=True, check=False)
    assert help_result.returncode == 0 and "--output" in help_result.stdout
    missing = subprocess.run([sys.executable, str(SOURCE)], env=env, capture_output=True, text=True, check=False)
    assert missing.returncode == 2 and "set EMB_ROOT" in missing.stderr
    script = """import builtins, importlib.util, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'gym_aloha', 'gymnasium', 'mujoco', 'numpy', 'torch', 'lerobot'}:
        raise RuntimeError('unexpected heavy import: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
spec = importlib.util.spec_from_file_location('export_act', sys.argv[1])
spec.loader.exec_module(importlib.util.module_from_spec(spec))
"""
    subprocess.run([sys.executable, "-c", script, str(SOURCE)], cwd=tmp_path, env=env, check=True)
    assert list(tmp_path.iterdir()) == []


def test_cli_failure_returns_nonzero_without_overwriting(tmp_path, monkeypatch):
    monkeypatch.setenv("EMB_ROOT", str(tmp_path))
    target = tmp_path / "already_used"
    target.mkdir()
    (target / "keep").write_text("original")
    assert exporter.main(["--output", str(target)]) == 1
    assert (target / "keep").read_text() == "original"


def test_invalid_metadata_cannot_publish_a_completion_marker(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter, "export_demo", lambda *args: {"trajectory": "demo.npz", "invalid": float("nan")})
    target = tmp_path / "invalid"
    with pytest.raises(ValueError):
        exporter.run(target, tmp_path / "checkpoint")
    assert (target / "failure.json").exists() and not (target / "done.json").exists()
