"""导出 ALOHA 场景为 .mjb,并用 ACT 跑一回合,记录每步 qpos 供 Mac 端回放。"""
import os

import gym_aloha  # noqa: F401
import gymnasium as gym
import mujoco
import numpy as np
import torch
from lerobot.configs.policies import PreTrainedConfig
from lerobot.envs.configs import AlohaEnv
from lerobot.envs.utils import preprocess_observation
from lerobot.policies.factory import make_policy, make_pre_post_processors

EMB = os.environ.get("EMB_ROOT", "/path/to/emb")

OUT = EMB + "/logs/viewer"; os.makedirs(OUT, exist_ok=True)
CKPT = EMB + "/ckpt/act_aloha_sim_transfer_cube_human@ba73b276_migrated"
env_cfg = AlohaEnv(task="AlohaTransferCube-v0")
env = gym.make("gym_aloha/AlohaTransferCube-v0", obs_type="pixels_agent_pos", render_mode="rgb_array")
phys = env.unwrapped._env.physics
mujoco.mj_saveModel(phys.model._model, f"{OUT}/aloha_transfer_cube.mjb", None)

cfg = PreTrainedConfig.from_pretrained(CKPT); cfg.pretrained_path = CKPT; cfg.device = "cuda"
policy = make_policy(cfg, env_cfg=env_cfg); policy.eval()
pre, post = make_pre_post_processors(cfg, pretrained_path=CKPT)
for seed in range(1000, 1010):
    obs, _ = env.reset(seed=seed); policy.reset(); qpos = [phys.data.qpos.copy()]; ok = False
    for _t in range(400):
        o = {k: (v[None] if isinstance(v, np.ndarray) else v) for k, v in obs.items()}
        o = {k: {kk: vv[None] for kk, vv in v.items()} if isinstance(v, dict) else v for k, v in obs.items()}
        batch = pre(preprocess_observation(o))
        with torch.inference_mode():
            a = post(policy.select_action(batch))
        obs, r, term, trunc, info = env.step(a[0].cpu().numpy())
        qpos.append(phys.data.qpos.copy())
        if info.get("is_success"): ok = True
        if term or trunc: break
    print(f"seed {seed}: steps {len(qpos)-1} success {ok}")
    if ok: break
np.savez_compressed(f"{OUT}/act_transfer_cube_seed{seed}.npz", qpos=np.array(qpos), dt=1/50, success=ok, seed=seed)
print("saved", OUT, os.listdir(OUT))
