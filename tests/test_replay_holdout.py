"""The packaged P2 loop must preserve exact source actions and stop correctly."""
from types import SimpleNamespace

import numpy as np
import pytest
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
