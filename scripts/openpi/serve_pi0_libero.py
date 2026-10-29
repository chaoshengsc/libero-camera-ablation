"""在 OpenPI 环境里加载官方 pi0_libero(原版 JAX 实现、官方归一化与增量还原),经本机端口给 LeRobot 评测提供动作块。
用法(OpenPI 环境): OPENPI_AUTHKEY=<口令> python serve_pi0_libero.py <检查点目录> <端口>
客户端是 scripts/eval/eval_probe.py(POLICY_SERVER=<端口>)。为什么不用 LeRobot 的转换版:见 docs/NOTES.md 2026-10-28。
预处理照 OpenPI examples/libero/main.py:图像(客户端已旋转 180°)resize_with_pad 到 224 再转 uint8;状态 = 末端位置 3 + 轴角 3 + 夹爪 2。
屏蔽槽位(客户端请求里的 drop):把 LiberoInputs 输出里该槽位的 image_mask 置为 False,与训练时空槽位(right_wrist_0_rgb)的处理相同。
通信用标准库 multiprocessing.connection,只监听 127.0.0.1;数组按 (字节, 形状, dtype) 传,不受两边 numpy 版本不同影响。"""
import os
import sys
from multiprocessing.connection import Listener

import numpy as np
from openpi.policies import libero_policy, policy_config
from openpi.training import config as _config
from openpi_client import image_tools

CKPT, PORT = sys.argv[1], int(sys.argv[2])
_drop = []  # 当前请求要屏蔽的槽位
_seen = {}  # 当前请求实际送进模型的掩码,回传给客户端作证据

_orig_inputs = libero_policy.LiberoInputs.__call__


def _inputs(self, data):
    out = _orig_inputs(self, data)
    for k in _drop:
        assert k in out["image_mask"], k
        out["image_mask"][k] = np.False_
    _seen["masks"] = {k: bool(v) for k, v in out["image_mask"].items()}
    return out


libero_policy.LiberoInputs.__call__ = _inputs


def arr(t):
    b, shape, dtype = t
    return np.frombuffer(b, dtype=dtype).reshape(shape)


def pack(a):
    a = np.ascontiguousarray(a)
    return a.tobytes(), a.shape, a.dtype.str


cfg = _config.get_config("pi0_libero")
policy = policy_config.create_trained_policy(cfg, CKPT)
print("loaded", CKPT, "| model:", cfg.model, flush=True)

with Listener(("127.0.0.1", PORT), authkey=os.environ["OPENPI_AUTHKEY"].encode()) as listener:
    print("ready on port", PORT, flush=True)
    while True:
        with listener.accept() as conn:
            print("client connected", flush=True)
            while True:
                try:
                    req = conn.recv()
                except EOFError:
                    print("client disconnected", flush=True)
                    break
                _drop[:] = req["drop"]
                obs = {
                    "observation/image": image_tools.convert_to_uint8(image_tools.resize_with_pad(arr(req["image"]), 224, 224)),
                    "observation/wrist_image": image_tools.convert_to_uint8(image_tools.resize_with_pad(arr(req["wrist_image"]), 224, 224)),
                    "observation/state": arr(req["state"]),
                    "prompt": req["prompt"],
                }
                out = policy.infer(obs)
                conn.send({"actions": pack(np.asarray(out["actions"], dtype=np.float32)), "masks": dict(_seen["masks"]),
                           "image_shape": obs["observation/image"].shape, "infer_ms": out["policy_timing"]["infer_ms"]})
