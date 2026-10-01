"""视觉依赖测试汇总:正常(500 回合评测里每任务前 10 次)vs 全涂黑(每任务 10 次),同种子同初始状态。"""
import glob
import json
import os
import re

EMB = os.environ.get("EMB_ROOT", "/path/to/emb")

E = EMB + "/logs/eval"

def lerobot(r, first=None):
    per = json.load(open(glob.glob(f"{E}/{r}/out/**/eval_info.json", recursive=True)[0]))["per_task"]
    return [sum(t["metrics"]["successes"][:first]) for t in per]

def openvla(r, first=None):
    txt = open(glob.glob(f"{E}/{r}/logs/*.txt")[0]).read()
    per = {}
    for task, ok in re.findall(r"Task: (.*?)\n.*?Success: (True|False)", txt, re.S):
        per.setdefault(task, []).append(ok == "True")
    return [sum(v[:first]) for v in per.values()]

rows = [("OpenVLA", openvla("openvla_spatial_500", 10), openvla("openvla_black_all")),
        ("SmolVLA", lerobot("smolvla_hfvla_500", 10), lerobot("smolvla_black_all")),
        ("pi0", lerobot("pi0_spatial_500", 10), lerobot("pi0_black_all")),
        ("pi0.5", lerobot("pi05_spatial_500", 10), lerobot("pi05_black_all"))]
out = []
for m, a, b in rows:
    print(f"{m:8} 正常 {sum(a):3}/100  涂黑 {sum(b):3}/100  下降 {sum(a) - sum(b):+d} 个百分点 | 正常 {a} | 涂黑 {b}")
    out.append({"model": m, "normal": a, "black": b})
json.dump(out, open(f"{E}/B_summary.json", "w"), ensure_ascii=False)
