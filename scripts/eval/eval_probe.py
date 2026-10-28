"""运行 lerobot-eval,并(1)按 BLACKOUT 涂黑送进策略的相机画面,(2)逐步记录末端执行器轨迹。不改 LeRobot 源码。
BLACKOUT=none(默认)| all | agent(只涂主视角)| wrist(只涂腕部相机)
         | noise(两路加高斯噪声,标准差 NOISE_STD,默认 0.1,像素范围 [0,1])
         | freeze(整个回合都给第 1 帧画面:真实、分布内,但不再更新)
         | freeze_wrist / freeze_agent(只冻结这一路:整个回合都给它第 1 帧的真实画面,另一路正常更新)
         | drop_wrist / drop_agent(去掉这一路相机:在 π0/π0.5 内部把该相机槽填 -1、注意力掩码设为 0,
           与训练时空相机槽的处理相同;涂黑则掩码仍为 1。不能直接从输入里删键:LeRobot 会把在场的图像排在前面、
           缺失的补在后面,删掉主视角时腕部画面会被挪进主视角的槽位)
TRAJ_OUT=<npz 路径>:每回合一条轨迹,字段 eef[T,3]、grip[T,2];按 rollout 调用顺序(batch_size=1 时即 任务0回合0..9, 任务1…)。"""
import atexit
import hashlib
import os
import sys

import lerobot.scripts.lerobot_eval as E
import numpy as np
import torch

MODE = os.environ.get("BLACKOUT", "none")
assert MODE in {"none", "all", "agent", "wrist", "noise", "freeze", "drop_wrist", "drop_agent", "freeze_wrist", "freeze_agent"}, f"unknown BLACKOUT={MODE}"
TRAJ_OUT = os.environ.get("TRAJ_OUT")
NOISE_STD = float(os.environ.get("NOISE_STD", "0.1"))
_first = {}
_step = [0]
_dropped = []  # drop_* 模式下要屏蔽的相机键
_masked = []  # π0/π0.5 的包装确实按槽位屏蔽过一次后置位;其他策略没有这层包装
_pre, _roll, _shown = E.preprocess_observation, E.rollout, False
episodes = []  # 每项:{"eef": [...], "grip": [...]}


def _hit(k):
    if MODE == "all":
        return True
    wrist = any(s in k for s in ("eye_in_hand", "wrist")) or k.endswith("image2")
    return wrist if MODE in ("wrist", "drop_wrist", "freeze_wrist") else not wrist


def pre(obs):
    global _shown
    st = obs.get("robot_state") if isinstance(obs, dict) else None
    if st is not None and episodes:
        assert len(st["eef"]["pos"]) == 1, "trajectory logging requires --eval.batch_size=1"
        episodes[-1]["eef"].append(np.asarray(st["eef"]["pos"])[0].copy())
        episodes[-1]["grip"].append(np.asarray(st["gripper"]["qpos"])[0].copy())
    out = _pre(obs)
    keys = [k for k in out if k.startswith("observation.image")]
    _step[0] += 1
    if episodes and "h0" not in episodes[-1]:  # 本回合第 1 帧主视角的哈希:用来核对两次运行的同一回合是否同一初始状态
        episodes[-1]["h0"] = hashlib.md5(out[keys[0]].cpu().numpy().round(3).tobytes()).hexdigest()[:12]
    if MODE == "noise":
        for k in keys:
            out[k] = (out[k] + NOISE_STD * torch.randn_like(out[k])).clamp(0, 1)
    elif MODE in ("freeze", "freeze_wrist", "freeze_agent"):
        hit = keys if MODE == "freeze" else [k for k in keys if _hit(k)]
        assert hit and (MODE == "freeze" or len(hit) == 1), f"{MODE}: expected one camera to freeze, got {hit}"
        if not _first:  # 本回合第 1 步:记下画面(roll() 在每回合开始时清空)
            _first.update({k: out[k].clone() for k in keys})
        for k in hit:
            out[k] = _first[k].clone()
        if len(episodes) == 1 and _step[0] == 20:  # 第 1 回合第 20 步(替换之后):冻结的那路应为 0,其余应大于 0
            print("[probe] freeze check at step 20, max |sent - frame1|:",
                  {k: round(float((out[k] - _first[k]).abs().max()), 4) for k in keys}, "(frozen:", hit, ")", flush=True)
    elif MODE.startswith("drop_"):
        hit = [k for k in keys if _hit(k)]
        assert len(hit) == 1, f"{MODE}: expected one camera to drop, got {hit}"
        # 第 1 步之后策略至少推理过一次;没屏蔽过说明策略不是 π0/π0.5,drop 会退化成涂黑
        assert _step[0] == 1 or _masked, f"{MODE} only works with π0/π0.5: the camera was not masked in its slot"
        _dropped[:] = hit
        out[hit[0]] = torch.zeros_like(out[hit[0]])  # 真正的屏蔽在 _log_masks 的包装里按槽位完成
    elif MODE != "none":
        for k in keys:
            if _hit(k):
                out[k] = torch.zeros_like(out[k])
    if not _shown:
        print(f"[probe] BLACKOUT={MODE} NOISE_STD={NOISE_STD}", {k: (tuple(v.shape), float(v.float().abs().max())) for k, v in out.items()
                                          if k.startswith("observation.image")}, "| robot_state:", st is not None, flush=True)
        _shown = True
    return out


def _log_masks():
    """π0/π0.5:drop_* 模式下在原槽位屏蔽该相机(填 -1、掩码 0);第一次进入策略时打印每个槽位的掩码与像素范围。"""
    from lerobot.policies.pi0.modeling_pi0 import PI0Policy
    from lerobot.policies.pi05.modeling_pi05 import PI05Policy
    _masks_shown = []
    for cls in (PI0Policy, PI05Policy):
        def wrapped(self, batch, _orig=cls._preprocess_images, _masks_shown=_masks_shown):
            images, masks = _orig(self, batch)
            slots = list(self.config.image_features)
            assert len(images) == len(slots) and all(k in batch for k in slots[:len(slots) - self.config.empty_cameras]), \
                "slot order assumption broken: a real camera is missing from the batch"
            for k in _dropped:
                i = slots.index(k)
                images[i] = torch.ones_like(images[i]) * -1
                masks[i] = torch.zeros_like(masks[i])
                _masked[:] = [True]
            if not _masks_shown:
                print("[probe] slots/mask/pixel range:", [(k.split(".")[-1], bool(m[0]), round(float(i.min()), 2), round(float(i.max()), 2))
                                                          for k, m, i in zip(slots, masks, images, strict=True)], flush=True)
                _masks_shown.append(True)
            return images, masks
        cls._preprocess_images = wrapped


def roll(*a, **k):
    episodes.append({"eef": [], "grip": []})
    _first.clear()
    _step[0] = 0
    return _roll(*a, **k)


def _save():
    if TRAJ_OUT and episodes:
        np.savez_compressed(TRAJ_OUT, n=len(episodes),
                            **{f"eef_{i}": np.array(e["eef"]) for i, e in enumerate(episodes)},
                            **{f"grip_{i}": np.array(e["grip"]) for i, e in enumerate(episodes)},
                            h0=np.array([e.get("h0", "") for e in episodes]))
        print(f"[probe] saved {len(episodes)} episodes -> {TRAJ_OUT}", flush=True)


# 入口保护:多进程以 spawn 方式启动时子进程会重新导入本文件,没有保护会重复执行主流程
if __name__ == "__main__":
    atexit.register(_save)
    E.preprocess_observation, E.rollout = pre, roll
    _log_masks()
    sys.exit(E.main())
