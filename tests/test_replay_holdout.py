"""The packaged P2 loop must preserve exact source actions and stop correctly."""
import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import replay_holdout as runner
from replay_holdout import check_self_gate, replay, run
from summarize_followup import array_hash


class FakeEnv:
    def __init__(self, success=None, terminated=None, truncated=None):
        self.stop = success, terminated, truncated
        self.count = 0
        self.sim = SimpleNamespace(data=SimpleNamespace(body_xpos=np.zeros((1, 3)), time=0.0),
                                   get_state=lambda: np.zeros(4))
        self._env = SimpleNamespace(env=SimpleNamespace(sim=self.sim, obj_body_id={"object": 0}))

    def observation(self):
        return {"pixels": {"image": np.zeros((2, 2, 3), dtype=np.uint8)},
                "robot_state": {"eef": {"pos": np.array([self.count, 0, 0])},
                                "gripper": {"qpos": np.zeros(2)}}}

    def reset(self, seed):
        self.seed = seed
        self.init_state_id += 1
        return self.observation(), {}

    def step(self, action):
        self.count += 1
        assert action.dtype == np.float64
        success, term, trunc = [s == self.count for s in self.stop]
        self.sim.data.time += 0.05
        return self.observation(), 0, term, trunc, {"is_success": success, "done": term}


@pytest.mark.parametrize("kwargs,reason,n", [
    ({"success": 2}, "success", 2),
    ({"terminated": 3}, "terminated", 3),
    ({"truncated": 4}, "truncated", 4),
    ({}, "sequence_exhausted", 6),
])
def test_replay_stops_and_exact_prefix(kwargs, reason, n):
    env = FakeEnv(**kwargs)
    a = np.arange(42, dtype=np.float32).reshape(6, 7)
    result, arrays = replay(env, 11, a)
    assert result["reason"] == reason and result["steps"] == n and env.seed == 1011
    assert result["success"] == (reason == "success")
    assert np.array_equal(arrays["actions"], a[:n].astype(np.float64))
    assert result["sent_action_hash"] == array_hash(a[:n].astype(np.float64))


def test_limit_and_dtype_hash():
    result, _ = replay(FakeEnv(), 49, np.zeros((300, 7), dtype=np.float32))
    assert result["reason"] == "episode_limit" and result["steps"] == 280
    a = np.zeros((2, 7), dtype=np.float32)
    assert array_hash(a) != array_hash(a.astype(np.float64))



def test_self_gate_and_no_overwrite(tmp_path):
    assert check_self_gate([{"success": i < 8} for i in range(10)]) == 8
    with pytest.raises(RuntimeError):
        check_self_gate([{"success": i < 7} for i in range(10)])
    with pytest.raises(FileExistsError):
        run(tmp_path)  # Must reject before importing/allocating a simulator.


@pytest.fixture
def simulated_runtime(monkeypatch):
    state = {"success": True, "environments": []}

    class LiberoEnv(FakeEnv):
        def __init__(self, *args, **kwargs):
            super().__init__(success=2 if state["success"] else None)
            self._init_states = range(50)
            self._max_episode_steps = 280
            self._reset_stride = 1
            self.closed = False
            state["environments"].append(self)

        def reset(self, seed):
            self.count = 0
            return super().reset(seed)

        def close(self):
            self.closed = True

    actions = [np.zeros((3, 7), dtype=np.float32) for _ in range(10)]
    selection = {"tasks": [{"source_initial": i % 10, "targets": list(range(10, 50)),
                            "action_hash": array_hash(actions[i])} for i in range(10)]}
    monkeypatch.setattr(runner, "load_replay_holdout", lambda: (selection, {}, actions))
    benchmark = SimpleNamespace(get_benchmark_dict=lambda: {"libero_spatial": lambda: object()})
    for name, module in {
        "mujoco": SimpleNamespace(__version__="3.3.2"),
        "lerobot.envs.libero": SimpleNamespace(LiberoEnv=LiberoEnv),
        "libero.libero": SimpleNamespace(benchmark=benchmark),
    }.items():
        monkeypatch.setitem(sys.modules, name, module)
    return state


def test_self_only_cannot_enter_formal_stage(tmp_path, simulated_runtime):
    output = tmp_path / "self"
    run(output, self_only=True)
    progress = json.loads((output / "progress.json").read_text())
    assert progress["status"] == "self_completed" and len(progress["self"]) == 10
    assert progress["formal"] == progress["invalid"] == []
    assert json.loads((output / "runtime.json").read_text())["mode"] == "self_only"
    assert json.loads((output / "self_gate.json").read_text()) == {"successes": 10, "n": 10, "passed": True}
    assert json.loads((output / "self_done.json").read_text()) == {"n": 10, "successes": 10}
    assert not (output / "done.json").exists()
    assert len(list((output / "episodes").glob("*.npz"))) == 10
    assert all(env.closed for env in simulated_runtime["environments"])


@pytest.mark.parametrize("self_only", [False, True])
def test_failed_self_gate_keeps_failure_and_stops(tmp_path, simulated_runtime, self_only):
    simulated_runtime["success"] = False
    output = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="Self-replay gate failed"):
        run(output, self_only=self_only)
    progress = json.loads((output / "progress.json").read_text())
    assert progress["status"] == "gate_failed" and len(progress["self"]) == 10
    assert progress["formal"] == []
    assert not (output / "self_done.json").exists() and not (output / "done.json").exists()
    assert all(env.closed for env in simulated_runtime["environments"])


def test_default_still_runs_all_frozen_targets(tmp_path, simulated_runtime):
    output = tmp_path / "full"
    run(output)
    progress = json.loads((output / "progress.json").read_text())
    assert progress["status"] == "completed" and len(progress["self"]) == 10
    assert [(r["task"], r["target"]) for r in progress["formal"]] == [(t, i) for t in range(10) for i in range(10, 50)]
    assert json.loads((output / "done.json").read_text()) == {"n": 400, "successes": 400}
    assert not (output / "self_done.json").exists()
    assert all(env.closed for env in simulated_runtime["environments"])


def test_cli_self_only_is_explicit(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(runner, "run", lambda output, self_only=False: calls.append((output, self_only)))
    output = tmp_path / "self"
    runner.main(["--output", str(output), "--self-only"])
    assert calls == [(output, True)]
