"""在本地用 MuJoCo 交互查看器回放策略轨迹。

准备:场景(.mjb)和轨迹(.npz)由 viewer/export_act.py 在 GPU 机器上生成,拷到 viewer/scenes/(这两类文件不入库)。
本地只需要 mujoco:  python3 -m venv .venv-viewer && .venv-viewer/bin/pip install mujoco

用法(macOS 必须用 mjpython 启动被动查看器):
  .venv-viewer/bin/mjpython viewer/replay.py viewer/scenes/aloha_transfer_cube.mjb viewer/scenes/act_transfer_cube_seed1001.npz
只看场景、不回放:省略第二个参数。

窗口里:鼠标左键拖动旋转,右键平移,滚轮缩放;空格暂停/继续;窗口关闭即退出。
"""
import sys
import time

import mujoco
import mujoco.viewer
import numpy as np

model = mujoco.MjModel.from_binary_path(sys.argv[1])
data = mujoco.MjData(model)
traj = np.load(sys.argv[2]) if len(sys.argv) > 2 else None
paused = False


def on_key(keycode):
    global paused
    if keycode == 32:  # 空格
        paused = not paused


with mujoco.viewer.launch_passive(model, data, key_callback=on_key) as v:
    if traj is None:
        mujoco.mj_forward(model, data)
        while v.is_running():
            v.sync()
            time.sleep(1 / 60)
    else:
        qpos, dt = traj["qpos"], float(traj["dt"])
        print(f"replaying {len(qpos)} steps, dt={dt}s, success={bool(traj['success'])}, seed={int(traj['seed'])}; looping")
        i = 0
        while v.is_running():
            t0 = time.time()
            if not paused:
                data.qpos[:] = qpos[i]
                mujoco.mj_forward(model, data)
                v.sync()
                i = (i + 1) % len(qpos)
            time.sleep(max(0.0, dt - (time.time() - t0)))
