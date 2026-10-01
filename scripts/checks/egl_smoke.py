import os
import time

print("MUJOCO_GL", os.environ.get("MUJOCO_GL"), "| EGL vendor file", os.environ.get("__EGL_VENDOR_LIBRARY_FILENAMES"))
import mujoco
from OpenGL import GL

ctx = mujoco.GLContext(640, 480); ctx.make_current()
print("GL_VENDOR  ", GL.glGetString(GL.GL_VENDOR).decode())
print("GL_RENDERER", GL.glGetString(GL.GL_RENDERER).decode())
print("GL_VERSION ", GL.glGetString(GL.GL_VERSION).decode())
ctx.free()
import gymnasium as gym
import imageio

env = gym.make("gym_aloha/AlohaInsertion-v0", obs_type="pixels", render_mode="rgb_array")
obs, _ = env.reset(seed=0)
t = time.time(); n = 50
for _ in range(n):
    obs, *_ = env.step(env.action_space.sample())
dt = time.time() - t
img = env.render()
print("frame", img.shape, img.dtype, "mean", round(float(img.mean()), 1), "std", round(float(img.std()), 1))
print(f"step+render {n/dt:.1f} it/s")
imageio.imwrite(os.environ["EMB_ROOT"] + "/logs/egl_smoke.png", img)
env.close()
