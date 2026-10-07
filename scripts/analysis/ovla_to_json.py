"""把 OpenVLA 的文本日志转成与 LeRobot eval_info.json 同结构的 JSON,并每任务挑 1 成功 + 1 失败的视频。
用法: python3 ovla_to_json.py [run_name, 默认 openvla_spatial_500] [novideo]
novideo:不挑视频(全涂黑评测的录像是送进模型的黑图,没有观看价值)。"""
import glob
import json
import os
import re
import shutil
import sys

EMB = os.environ.get("EMB_ROOT", "/path/to/emb")

RUN = sys.argv[1] if len(sys.argv) > 1 else "openvla_spatial_500"
NOVIDEO = "novideo" in sys.argv[2:]
W = f"{EMB}/logs/eval/{RUN}"
OUT = f"{W}/dash"; shutil.rmtree(OUT, ignore_errors=True); os.makedirs(f"{OUT}/videos", exist_ok=True)
txt = open(glob.glob(f"{W}/logs/*.txt")[0]).read()
eps = re.findall(r"Task: (.*?)\n.*?Saved rollout MP4 at path (\S+).*?Success: (True|False)", txt, re.S)
tasks = {}
for desc, mp4, ok in eps:
    tasks.setdefault(desc, []).append((mp4.replace("./", f"{W}/", 1), ok == "True"))
per_task = []
for tid, (desc, lst) in enumerate(tasks.items()):
    succ = [ok for _, ok in lst]; vids = []
    picks = [next((x for x in lst if x[1]), None), next((x for x in lst if not x[1]), None)]
    for _k, p in enumerate(p for p in picks if p and not NOVIDEO):
        dst = f"videos/task{tid}_{'ok' if p[1] else 'fail'}.mp4"; shutil.copy(p[0], f"{OUT}/{dst}")
        vids.append({"src": dst, "ep": lst.index(p), "success": p[1]})
    per_task.append({"task_group": "libero_spatial", "task_id": tid, "task": desc,
                     "metrics": {"successes": succ}, "videos": vids})
allok = [ok for t in per_task for ok in t["metrics"]["successes"]]
json.dump({"overall": {"pc_success": 100 * sum(allok) / len(allok), "n_episodes": len(allok)}, "per_task": per_task},
          open(f"{OUT}/eval_info.json", "w"), ensure_ascii=False, indent=1)
print("episodes", len(allok), "success", sum(allok), "videos", sum(len(t["videos"]) for t in per_task))
