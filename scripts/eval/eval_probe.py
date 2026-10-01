"""运行 lerobot-eval,并(1)按 BLACKOUT 涂黑送进策略的相机画面,(2)逐步记录末端执行器轨迹。不改 LeRobot 源码。
BLACKOUT=none(默认)| all | agent(只涂主视角)| wrist(只涂腕部相机)
         | noise(两路加高斯噪声,标准差 NOISE_STD,默认 0.1,像素范围 [0,1])
         | freeze(整个回合都给第 1 帧画面:真实、分布内,但不再更新)
TRAJ_OUT=<npz 路径>:每回合一条轨迹,字段 eef[T,3]、grip[T,2];按 rollout 调用顺序(batch_size=1 时即 任务0回合0..9, 任务1…)。"""
import atexit
import os
import sys

import lerobot.scripts.lerobot_eval as E
import numpy as np
import torch

MODE = os.environ.get("BLACKOUT", "none")
assert MODE in {"none", "all", "agent", "wrist", "noise", "freeze"}, f"unknown BLACKOUT={MODE}"
TRAJ_OUT = os.environ.get("TRAJ_OUT")
NOISE_STD = float(os.environ.get("NOISE_STD", "0.1"))
_first = {}
_pre, _roll, _shown = E.preprocess_observation, E.rollout, False
episodes = []  # 每项:{"eef": [...], "grip": [...]}


def _hit(k):
    if MODE == "all":
        return True
    wrist = any(s in k for s in ("eye_in_hand", "wrist")) or k.endswith("image2")
    return wrist if MODE == "wrist" else not wrist


def pre(obs):
    global _shown
    st = obs.get("robot_state") if isinstance(obs, dict) else None
    if st is not None and episodes:
        assert len(st["eef"]["pos"]) == 1, "trajectory logging requires --eval.batch_size=1"
        episodes[-1]["eef"].append(np.asarray(st["eef"]["pos"])[0].copy())
        episodes[-1]["grip"].append(np.asarray(st["gripper"]["qpos"])[0].copy())
    out = _pre(obs)
    keys = [k for k in out if k.startswith("observation.image")]
    if MODE == "noise":
        for k in keys:
            out[k] = (out[k] + NOISE_STD * torch.randn_like(out[k])).clamp(0, 1)
    elif MODE == "freeze":
        if not _first:  # 本回合第 1 步:记下画面(roll() 在每回合开始时清空)
            _first.update({k: out[k].clone() for k in keys})
        for k in keys:
            out[k] = _first[k].clone()
    elif MODE != "none":
        for k in keys:
            if _hit(k):
                out[k] = torch.zeros_like(out[k])
    if not _shown:
        print(f"[probe] BLACKOUT={MODE} NOISE_STD={NOISE_STD}", {k: (tuple(v.shape), float(v.float().abs().max())) for k, v in out.items()
                                          if k.startswith("observation.image")}, "| robot_state:", st is not None, flush=True)
        _shown = True
    return out


def roll(*a, **k):
    episodes.append({"eef": [], "grip": []})
    _first.clear()
    return _roll(*a, **k)


def _save():
    if TRAJ_OUT and episodes:
        np.savez_compressed(TRAJ_OUT, n=len(episodes),
                            **{f"eef_{i}": np.array(e["eef"]) for i, e in enumerate(episodes)},
                            **{f"grip_{i}": np.array(e["grip"]) for i, e in enumerate(episodes)})
        print(f"[probe] saved {len(episodes)} episodes -> {TRAJ_OUT}", flush=True)


# 入口保护:多进程以 spawn 方式启动时子进程会重新导入本文件,没有保护会重复执行主流程
if __name__ == "__main__":
    atexit.register(_save)
    E.preprocess_observation, E.rollout = pre, roll
    sys.exit(E.main())
