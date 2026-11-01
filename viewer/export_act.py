"""Export one ACT demonstration for the local viewer without replacing outputs.

Run in the configured lerobot environment with EMB_ROOT set. Try seeds 1000–1009
in order, stopping at the first success; retain only that trial, or the last
failure if none succeeds. This selection is for visualization, not evaluation.
The default output is $EMB_ROOT/logs/viewer and must not already exist. Use
--output with a fresh directory for another export. Failed artifacts are kept.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def export_demo(output, checkpoint):
    """The existing ACT rollout, called only after exclusive output reservation."""
    import gym_aloha  # noqa: F401
    import gymnasium as gym
    import mujoco
    import numpy as np
    import torch
    from lerobot.configs.policies import PreTrainedConfig
    from lerobot.envs.configs import AlohaEnv
    from lerobot.envs.utils import preprocess_observation
    from lerobot.policies.factory import make_policy, make_pre_post_processors

    env_cfg = AlohaEnv(task="AlohaTransferCube-v0")
    env = gym.make("gym_aloha/AlohaTransferCube-v0", obs_type="pixels_agent_pos", render_mode="rgb_array")
    try:
        phys = env.unwrapped._env.physics
        scene = "aloha_transfer_cube.mjb"
        mujoco.mj_saveModel(phys.model._model, str(output / scene), None)
        cfg = PreTrainedConfig.from_pretrained(str(checkpoint))
        cfg.pretrained_path = str(checkpoint)
        cfg.device = "cuda"
        policy = make_policy(cfg, env_cfg=env_cfg)
        policy.eval()
        pre, post = make_pre_post_processors(cfg, pretrained_path=str(checkpoint))
        attempts = []
        for seed in range(1000, 1010):
            obs, _ = env.reset(seed=seed)
            policy.reset()
            qpos = [phys.data.qpos.copy()]
            ok = False
            for _ in range(400):
                o = {k: {kk: vv[None] for kk, vv in v.items()} if isinstance(v, dict) else v for k, v in obs.items()}
                batch = pre(preprocess_observation(o))
                with torch.inference_mode():
                    action = post(policy.select_action(batch))
                obs, _, term, trunc, info = env.step(action[0].cpu().numpy())
                qpos.append(phys.data.qpos.copy())
                if info.get("is_success"):
                    ok = True
                if term or trunc:
                    break
            attempts.append({"seed": seed, "steps": len(qpos) - 1, "success": ok})
            print(f"seed {seed}: steps {len(qpos) - 1} success {ok}")
            if ok:
                break
        positions = np.asarray(qpos)
        if not np.isfinite(positions).all():
            raise ValueError("Non-finite positions; keep the failed export for review")
        trajectory = f"act_transfer_cube_seed{seed}.npz"
        np.savez_compressed(output / trajectory, qpos=positions, dt=1 / 50, success=ok, seed=seed)
        return {"scope": "demonstration_only", "selection": "first success, otherwise last failure",
                "attempts": attempts, "selected_seed": seed, "success": ok, "scene": scene,
                "trajectory": trajectory, "mujoco_version": mujoco.__version__}
    finally:
        env.close()


def run(output, checkpoint):
    output, checkpoint = Path(output), Path(checkpoint)
    output.mkdir(parents=True, exist_ok=False)  # Reject files, directories and symlinks before simulator/model imports.
    try:
        result = export_demo(output, checkpoint)
        result["completed_utc"] = datetime.now(timezone.utc).isoformat()
        serialized = json.dumps(result, indent=2, allow_nan=False)
        temporary = output / "done.json.tmp"
        with temporary.open("x") as file:
            file.write(serialized)
        temporary.replace(output / "done.json")
        return result
    except BaseException as error:
        with (output / "failure.json").open("x") as file:
            json.dump({"error": repr(error)}, file, indent=2)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Unused output directory; defaults to $EMB_ROOT/logs/viewer")
    args = parser.parse_args(argv)
    if not os.environ.get("EMB_ROOT"):
        parser.error("set EMB_ROOT to the configured working directory")
    root = Path(os.environ["EMB_ROOT"])
    try:
        result = run(args.output or root / "logs/viewer", root / "ckpt/act_aloha_sim_transfer_cube_human@ba73b276_migrated")
    except Exception as error:
        print(f"export failed: {error}", file=sys.stderr)
        return 1
    print(f"saved {result['trajectory']}; demonstration only, not an evaluation result")
    return 0


if __name__ == "__main__":
    sys.exit(main())
