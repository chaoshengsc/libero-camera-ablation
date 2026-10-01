"""把一个任务的末端轨迹(俯视 XY,单位 cm)导出成小 JSON,供 make_figures.py 画图。
用法: python3 export_trajectories.py [task_id]   (默认任务 1;需要 numpy 和 $EMB_ROOT/logs/eval/traj_*/traj.npz)"""
import json
import sys
from pathlib import Path

from analyze_trajectories import load

from metrics import grasp

RUNS = ["traj_pi0_normal", "traj_pi0_normal2", "traj_pi0_black"]

if __name__ == "__main__":
    task = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    out = {"task": task, "unit": "cm", "runs": {}}
    for run in RUNS:
        eps = load(run)[task * 10:(task + 1) * 10]
        out["runs"][run] = []
        for eef, grip, ok in eps:
            g = grasp(eef, grip)
            out["runs"][run].append({"success": ok, "xy": [[round(float(x), 1), round(float(y), 1)] for x, y, _ in eef[::2]],
                                     "grasp": None if g is None else [round(float(g[0]), 1), round(float(g[1]), 1)]})
    dst = Path(__file__).resolve().parents[2] / "results" / f"trajectories_task{task}.json"
    dst.write_text(json.dumps(out, separators=(",", ":")))
    print("wrote", dst, dst.stat().st_size, "bytes")
