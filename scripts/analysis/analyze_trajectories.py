"""用末端执行器轨迹检验 π0 看不见时是否执行"平均解法"。
轨迹来自 eval_probe.py(每回合 eef[T,3]、grip[T,2]),回合顺序 = 任务0回合0..9, 任务1…,同种子同初始状态。
指标(单位 cm):
  DTW  —— 动态时间规整后的平均点距,消除快慢差异,只比路线
  抓取点 —— 夹爪第一次明显合拢时的末端位置(模型"认为碗在哪")
  抓取点离散度 —— 同一任务 10 个回合抓取点到其均值的平均距离;看画面的策略应随碗的位置变化而分散,看不见则聚成一团"""
import glob
import json
import os

import numpy as np

from metrics import dtw, grasp, spread

EMB = os.environ["EMB_ROOT"]
E = EMB + "/logs/eval"


def load(run):
    z = np.load(f"{E}/{run}/traj.npz")
    per = json.load(open(glob.glob(f"{E}/{run}/out/**/eval_info.json", recursive=True)[0]))["per_task"]
    succ = [s for t in per for s in t["metrics"]["successes"]]
    assert int(z["n"]) == len(succ), f"{run}: {int(z['n'])} trajectories but {len(succ)} evaluated episodes; cannot pair by index"
    return [(z[f"eef_{i}"] * 100, z[f"grip_{i}"], bool(succ[i])) for i in range(int(z["n"]))]


if __name__ == "__main__":
    runs = {r: load(r) for r in ["traj_pi0_normal", "traj_pi0_normal2", "traj_pi0_black", "traj_pi05_normal"]}
    pairs = {"噪声底线 π0正常 vs π0正常(重跑)": ("traj_pi0_normal", "traj_pi0_normal2"),
             "π0 全涂黑 vs π0 正常": ("traj_pi0_black", "traj_pi0_normal"),
             "不同模型 π0.5 vs π0(都正常)": ("traj_pi05_normal", "traj_pi0_normal")}
    res = {}
    for name, (a, b) in pairs.items():
        ds = [dtw(runs[a][i][0], runs[b][i][0]) for i in range(100)]
        gt = [[np.linalg.norm(ga - gb) for i in range(t * 10, (t + 1) * 10)
               for ga, gb in [(grasp(*runs[a][i][:2]), grasp(*runs[b][i][:2]))] if ga is not None and gb is not None] for t in range(10)]
        gd = [x for g in gt for x in g]
        res[name] = {"dtw_mean": float(np.mean(ds)), "grasp_dist_mean": float(np.mean(gd)), "n_grasp_pairs": len(gd),
                     "dtw_by_task": [float(np.mean(ds[t * 10:(t + 1) * 10])) for t in range(10)],
                     "grasp_dist_by_task": [float(np.mean(g)) if g else None for g in gt]}
        print(f"{name:34} DTW {np.mean(ds):5.2f} cm   grasp-point distance {np.mean(gd):5.2f} cm (n={len(gd)})")

    print("\nGrasp-point spread (10 episodes of a task, cm):")
    sp = {}
    for r in runs:
        s = [spread([grasp(*runs[r][t * 10 + k][:2]) for k in range(10)]) for t in range(10)]
        sp[r] = s
        print(f"  {r:18} mean {np.nanmean(s):4.2f}   per task {[round(x, 1) for x in s]}")
    succ = {r: [sum(e[2] for e in runs[r][t * 10:(t + 1) * 10]) for t in range(10)] for r in runs}
    json.dump({"pairs": res, "grasp_spread": sp, "successes_by_task": succ}, open(f"{E}/traj_analyze.json", "w"), ensure_ascii=False)
