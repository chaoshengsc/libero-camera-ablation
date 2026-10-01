"""打印若干次评测的成功率与 95% 置信区间。用法: python3 summarize_eval.py <run_name> [<run_name> ...]"""
import glob
import json
import math
import os
import sys

EMB = os.environ.get("EMB_ROOT", "/path/to/emb")

for r in sys.argv[1:]:
    f = glob.glob(f"{EMB}/logs/eval/{r}/**/eval_info.json", recursive=True)
    if not f:
        print(r, "no eval_info.json"); continue
    d = json.load(open(f[0])); o = d["overall"]
    p, n = o["pc_success"], o["n_episodes"]
    ci = 196 * math.sqrt(p / 100 * (1 - p / 100) / n)
    extra = f"  avg_max_reward={o['avg_max_reward']:.3f}" if "pusht" in r else ""
    print(f"== {r}: {p:.1f}%  (n={n}, 95%CI ±{ci:.1f}){extra}  {o['eval_ep_s']:.1f}s per episode")
    tasks = d.get("per_task", [])
    if len(tasks) > 1:
        print("   per task:", " ".join(f"{sum(t['metrics']['successes'])}/{len(t['metrics']['successes'])}" for t in tasks))
