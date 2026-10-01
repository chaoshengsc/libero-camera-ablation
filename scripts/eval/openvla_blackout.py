"""OpenVLA 视觉依赖测试:替换 run_libero_eval 里的 get_libero_image,返回同尺寸全黑图。不改 openvla 源码。"""
import sys

import experiments.robot.libero.run_libero_eval as R
import numpy as np

_orig, _shown = R.get_libero_image, False

def black(obs, resize_size):
    global _shown
    img = _orig(obs, resize_size)
    if not _shown:
        print(f"[blackout] openvla image {img.shape} {img.dtype} -> zeros", flush=True); _shown = True
    return np.zeros_like(img)

# 入口保护:多进程以 spawn 方式启动时子进程会重新导入本文件,没有保护会重复执行主流程
if __name__ == "__main__":
    R.get_libero_image = black
    sys.exit(R.eval_libero())
