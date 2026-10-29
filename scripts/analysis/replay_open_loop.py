"""不用任何模型的开环回放基线:把一次评测里记录的动作序列,原样回放到同一任务的其他初始状态上。
回答“LIBERO-Spatial 上不看画面、每个任务重复一套固定动作，能成功多少”，并记录每个初始状态下物体的位置(场景变化量)。

用法(LeRobot 环境,需 EGL): python replay_open_loop.py <traj.npz> <eval_info.json> <每任务回合数> <输出.json> [self_only]
traj.npz 来自 eval_probe.py 的 TRAJ_OUT(含 act_i);回合顺序为 任务0回合0..n-1, 任务1…,回合 e 用第 e 个官方初始状态。
- 自回放(对照):成功回合的动作回放到它自己的初始状态上,应当同样成功,用来检验回放本身是确定的;
- 交叉回放:回放到同一任务的其他初始状态上。
环境与评测相同(LeRobot LiberoEnv、libero_spatial、开头 10 步空动作、相对控制);渲染分辨率不影响物理,取 128 以加快。
回放并非逐位确定:接触阶段会出现毫米级偏离(试跑见 docs/NOTES.md 2026-10-29),所以自回放成功率就是这个基线的噪声底线。"""
import json
import sys

import numpy as np
from lerobot.envs.libero import LiberoEnv
from libero.libero import benchmark

TRAJ, INFO, N, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
SELF_ONLY = len(sys.argv) > 5 and sys.argv[5] == "self_only"  # 试跑:只做自回放,检验回放是否确定,不看交叉结果
z = np.load(TRAJ)
per = sorted(json.load(open(INFO))["per_task"], key=lambda t: t["task_id"])
succ = [[bool(x) for x in t["metrics"]["successes"]] for t in per]
assert int(z["n"]) == 10 * N and all(len(s) == N for s in succ)
suite = benchmark.get_benchmark_dict()["libero_spatial"]()


def objects(env):
    """当前场景里各物体的位置(m)。"""
    inner = env._env.env
    return {k: [round(float(v), 5) for v in inner.sim.data.body_xpos[i]] for k, i in inner.obj_body_id.items()}


def replay(env, target, actions):
    """与评测相同:同一任务复用一个环境,按初始状态序号 reset(评测里 batch_size=1 时也是一个环境依次 reset)。"""
    env.init_state_id = target
    env.reset(seed=1000 + target)  # 与评测相同:seed 1000,每任务第 e 回合用 1000 + e
    for a in actions:
        _, _, _, _, info = env.step(np.asarray(a, dtype=np.float64))
        if info["is_success"]:
            return True
    return False


res = {"n_per_task": N, "tasks": []}
for t in range(10):
    env = LiberoEnv(suite, t, "libero_spatial", obs_type="pixels_agent_pos", observation_width=128, observation_height=128)
    acts = [z[f"act_{t * N + e}"] for e in range(N)]
    row = {"task": t, "source_success": succ[t], "self": {}, "cross": {}, "objects": []}
    for j in range(len(env._init_states)):  # 场景变化量:该任务全部官方初始状态下的物体位置
        env.init_state_id = j
        env.reset(seed=1000 + j)
        row["objects"].append(objects(env))
    for e in range(N):
        if succ[t][e]:
            row["self"][e] = replay(env, e, acts[e])
            if not SELF_ONLY:
                row["cross"][e] = {j: replay(env, j, acts[e]) for j in range(N) if j != e}
    env.close()
    print(f"task {t}: sources {sum(succ[t])}, self {sum(row['self'].values())}/{len(row['self'])}, "
          f"cross {sum(v for d in row['cross'].values() for v in d.values())}/{sum(len(d) for d in row['cross'].values())}", flush=True)
    res["tasks"].append(row)
json.dump(res, open(OUT, "w"))
print("wrote", OUT)
