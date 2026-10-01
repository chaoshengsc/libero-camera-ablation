"""方向 2 汇总:只涂主视角 / 只涂腕部 / 全涂黑 vs 正常(正常取 500 回合评测每任务前 10 次,同种子同初始状态)。"""
import glob
import json
import os
import re

EMB = os.environ.get("EMB_ROOT", "/path/to/emb")

E = EMB + "/logs/eval"


def r(run, first=None):
    per = json.load(open(glob.glob(f"{E}/{run}/out/**/eval_info.json", recursive=True)[0]))["per_task"]
    s = [sum(t["metrics"]["successes"][:first]) for t in per]
    return sum(s), s


for run in ["traj_pi0_agent", "traj_pi0_wrist"]:
    line = next(l for l in open(f"{E}/{run}/stdout.log", errors="ignore") if "[probe] BLACKOUT" in l)
    print(run, re.findall(r"'(observation\.images\.\w+)': \(\([0-9, ]+\), ([0-9.]+)\)", line))

rows = [("pi0", "pi0_spatial_500", "traj_pi0_agent", "traj_pi0_wrist", "pi0_black_all"),
        ("pi0.5", "pi05_spatial_500", "traj_pi05_agent", "traj_pi05_wrist", "pi05_black_all"),
        ("SmolVLA", "smolvla_hfvla_500", "traj_smol_agent", "traj_smol_wrist", "smolvla_black_all")]
out = []
print("model    normal  agent_black  wrist_black  all_black")
for m, n, a, w, b in rows:
    x = [r(n, 10)[0], r(a)[0], r(w)[0], r(b)[0]]
    print(f"{m:8} {x[0]:>6} {x[1]:>12} {x[2]:>12} {x[3]:>10}   agent {r(a)[1]}  wrist {r(w)[1]}")
    out.append({"model": m, "normal": x[0], "agent_black": x[1], "wrist_black": x[2], "all_black": x[3]})
json.dump(out, open(f"{E}/cam_summary.json", "w"))
