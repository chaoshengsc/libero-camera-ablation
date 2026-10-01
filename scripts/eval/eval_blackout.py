"""视觉依赖测试:运行 lerobot-eval,但把送进策略的相机画面换成全黑。不改 LeRobot 源码。
BLACKOUT=all(默认)| agent(只涂主视角)| wrist(只涂腕部相机)。录像来自环境原始渲染,不受影响。"""
import os
import sys

import lerobot.scripts.lerobot_eval as E
import torch

MODE = os.environ.get("BLACKOUT", "all")
_orig, _shown = E.preprocess_observation, False

def _hit(k):
    if MODE == "all":
        return True
    wrist = any(s in k for s in ("eye_in_hand", "wrist")) or k.endswith("image2")
    return wrist if MODE == "wrist" else not wrist

def patched(obs):
    global _shown
    out = _orig(obs)
    for k in [k for k in out if k.startswith("observation.image")]:
        if _hit(k):
            out[k] = torch.zeros_like(out[k])
    if not _shown:
        print(f"[blackout:{MODE}]", {k: (tuple(v.shape), float(v.float().abs().max())) for k, v in out.items() if k.startswith("observation.image")}, flush=True)
        _shown = True
    return out

# 入口保护:多进程以 spawn 方式启动时子进程会重新导入本文件,没有保护会重复执行主流程
if __name__ == "__main__":
    E.preprocess_observation = patched
    sys.exit(E.main())
