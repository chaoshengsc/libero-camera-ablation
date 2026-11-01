"""Repeat the frozen P2 replay protocol; no policy or model inference.

Run only in the configured LIBERO/EGL environment. Source selection and actions
are bundled under dashboard/data/replay_holdout; output must be a new directory.
The replay loop below is the loop used by the audited P2 run.
Use --self-only for the ten self-replays without entering the formal stage.
"""

import argparse
import inspect
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from summarize_followup import array_hash, load_replay_holdout, sha


def save(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def check_self_gate(rows):
    assert len(rows) == 10
    count = sum(r["success"] for r in rows)
    if count < 8:
        raise RuntimeError(f"Self-replay gate failed: {count}/10; do not start formal replay")
    return count


def replay(env, target, actions):
    """Stop on success, termination, truncation, 280 steps, or sequence exhaustion."""
    env.init_state_id = target
    obs, _ = env.reset(seed=1000 + target)
    assert env.init_state_id == target + 1
    frames = {k: array_hash(v) for k, v in obs["pixels"].items()}
    eef0 = np.array(obs["robot_state"]["eef"]["pos"], copy=True)
    sim = env._env.env.sim
    initial_state = sim.get_state().flatten().copy()
    object_ids = env._env.env.obj_body_id
    object_names = sorted(object_ids)
    initial_objects = np.array([sim.data.body_xpos[object_ids[k]] for k in object_names])
    sent, eef, grip, flags, objects, times = [], [], [], [], [], []
    reason = "sequence_exhausted"
    success = False
    for i, source_action in enumerate(actions):
        if i >= 280:
            reason = "episode_limit"
            break
        a = np.array(source_action, dtype=np.float64, copy=True)
        sent.append(a.copy())
        observation, _, terminated, truncated, info = env.step(a)
        success = bool(info["is_success"])
        flags.append([success, bool(terminated), bool(truncated), bool(info.get("done", False))])
        eef.append(np.array(observation["robot_state"]["eef"]["pos"], copy=True))
        grip.append(np.array(observation["robot_state"]["gripper"]["qpos"], copy=True))
        objects.append(np.array([sim.data.body_xpos[object_ids[k]] for k in object_names]))
        times.append(float(sim.data.time))
        if success or terminated or truncated:
            reason = "success" if success else ("terminated" if terminated else "truncated")
            break
    if len(sent) == 280 and not any(flags[-1][:3]):
        reason = "episode_limit"
    sent = np.asarray(sent)
    assert np.array_equal(sent, actions[:len(sent)].astype(np.float64))
    arrays = {"actions": sent, "eef": np.asarray(eef), "grip": np.asarray(grip),
              "flags": np.asarray(flags, dtype=bool), "sim_time": np.asarray(times),
              "object_positions": np.asarray(objects), "object_names": np.asarray(object_names),
              "initial_objects": initial_objects, "initial_sim_state": initial_state, "eef0": eef0}
    for a in arrays.values():
        if a.dtype.kind in "fiu":
            assert np.isfinite(a).all()
    return {"target": target, "seed": 1000 + target, "success": success,
            "valid": True, "steps": len(sent), "reason": reason,
            "initial_state_hash": array_hash(initial_state), "first_frame_hashes_128": frames,
            "eef0": eef0.tolist(), "sent_action_hash": array_hash(sent)}, arrays


def run(output, self_only=False):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)  # Reject existing output before importing the simulator.
    (output / "episodes").mkdir()
    selection, _, actions = load_replay_holdout()
    import mujoco
    from lerobot.envs.libero import LiberoEnv
    from libero.libero import benchmark

    assert mujoco.__version__ == "3.3.2", "P2 requires the recorded MuJoCo 3.3.2 runtime"
    runtime = {"started_utc": datetime.now(timezone.utc).isoformat(), "pid": os.getpid(),
               "mode": "self_only" if self_only else "full",
               "python": sys.version, "mujoco": mujoco.__version__, "runner_sha256": sha(__file__),
               "libero_env_sha256": sha(inspect.getsourcefile(LiberoEnv)), "selection": selection}
    save(output / "runtime.json", runtime)
    suite = benchmark.get_benchmark_dict()["libero_spatial"]()
    progress = {"status": "running", "self": [], "formal": [], "invalid": []}
    environments = {}
    active = None
    started = time.monotonic()
    try:
        for stage in (("self",) if self_only else ("self", "formal")):
            for task, row in enumerate(selection["tasks"]):
                if task not in environments:
                    env = LiberoEnv(suite, task, "libero_spatial", obs_type="pixels_agent_pos",
                                    observation_width=128, observation_height=128, num_steps_wait=10,
                                    control_freq=20, control_mode="relative", hard_reset=True)
                    assert len(env._init_states) >= 50 and env._max_episode_steps == 280
                    assert env._reset_stride == 1
                    environments[task] = env
                env = environments[task]
                targets = [row["source_initial"]] if stage == "self" else row["targets"]
                for target in targets:
                    active = {"stage": stage, "task": task, "target": target}
                    result, arrays = replay(env, target, actions[task])
                    name = f"{stage}_t{task:02d}_i{target:02d}.npz"
                    np.savez_compressed(output / "episodes" / name, **arrays)
                    result.update(task=task, source_initial=row["source_initial"],
                                  source_action_hash=row["action_hash"], source_length=len(actions[task]),
                                  evidence_file=f"episodes/{name}", evidence_sha256=sha(output / "episodes" / name))
                    progress[stage].append(result)
                    progress["elapsed_seconds"] = time.monotonic() - started
                    save(output / "progress.json", progress)
                    print(f"{stage} task={task} target={target} success={result['success']} "
                          f"completed={len(progress[stage])}", flush=True)
                if self_only or stage == "formal":
                    env.close()
                    del environments[task]
            if stage == "self":
                try:
                    count = check_self_gate(progress["self"])
                except RuntimeError:
                    progress["status"] = "gate_failed"
                    raise
                save(output / "self_gate.json", {"successes": count, "n": 10, "passed": True})
        expected = [] if self_only else [(t, i) for t in range(10) for i in range(10, 50)]
        assert [(r["task"], r["target"]) for r in progress["formal"]] == expected
    except BaseException as error:
        if progress["status"] != "gate_failed":
            progress["status"] = "technical_failure"
            progress["invalid"].append({**(active or {}), "error": repr(error), "traceback": traceback.format_exc()})
        save(output / "progress.json", progress)
        raise
    finally:
        for env in environments.values():
            env.close()
    progress["status"] = "self_completed" if self_only else "completed"
    save(output / "progress.json", progress)
    stage, marker = ("self", "self_done.json") if self_only else ("formal", "done.json")
    save(output / marker, {"n": len(progress[stage]), "successes": sum(r["success"] for r in progress[stage])})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New isolated output directory; existing paths are rejected")
    parser.add_argument("--self-only", action="store_true", help="Run only ten self-replays and their gate; never start formal targets")
    args = parser.parse_args(argv)
    run(args.output, self_only=args.self_only)


if __name__ == "__main__":
    main()
