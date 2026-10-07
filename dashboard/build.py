"""把 data/ 下各次评测的结果汇总成 results.js,供 index.html 读取。

用法: python3 build.py
每新增一次评测:把评测输出同步到 data/<id>/(至少含 eval_info.json,可带 videos/),再在 RUNS 里加一项。
eval_info.json 为 LeRobot 结构(overall / per_task[].metrics);OpenVLA 的文本日志已在工作站转成同结构。
"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).parent

RUNS = [
    {"id": "act_cube_500", "model": "ACT", "task": "ALOHA Transfer Cube", "sim": "MuJoCo",
     "checkpoint": "lerobot/act_aloha_sim_transfer_cube_human@ba73b276",
     "baseline_pc": 83.0, "baseline_n": 500, "baseline_src": "HF 仓库自带 eval_info.json(500 回合)"},
    {"id": "openvla_spatial_500", "model": "OpenVLA", "task": "LIBERO-Spatial", "sim": "MuJoCo",
     "checkpoint": "openvla/openvla-7b-finetuned-libero-spatial@962318ce",
     "baseline_pc": 84.7, "baseline_pm": 0.9, "baseline_src": "openvla README(3 种子 × 500 回合,A100)"},
    {"id": "smolvla2_spatial_500", "model": "SmolVLA", "task": "LIBERO-Spatial", "sim": "MuJoCo",
     "checkpoint": "lerobot/smolvla_libero@31d453f7",
     "baseline_pc": 90.0, "baseline_n": 100,
     "baseline_src": "SmolVLA 论文 Table 2(每任务 10 次);该权重只在 LIBERO-Spatial 上训练,评测用 n_action_steps=10"},
    {"id": "pi05_spatial_500", "model": "π0.5", "task": "LIBERO-Spatial", "sim": "MuJoCo",
     "checkpoint": "lerobot/pi05_libero_finetuned_v044@8e174154",
     "baseline_pc": 98.8, "baseline_src": "OpenPI LIBERO README(LeRobot 文档复现为 97.0%)"},
    {"id": "dp_pusht_500", "model": "Diffusion Policy", "task": "PushT", "sim": "2D(pymunk)",
     "checkpoint": "lerobot/diffusion_pusht@84a7c231",
     "baseline_pc": 65.4, "baseline_n": 500, "baseline_src": "LeRobot 模型卡(500 回合;原版 DP 仓库同等模型 64.2%)"},
]

LIBERO_SPATIAL_TASKS = [
    "盘子与小烤碗之间", "小烤碗旁", "桌子中央", "饼干盒上", "木柜上层抽屉里",
    "小烤碗上", "饼干盒旁", "灶台上", "盘子旁", "木柜顶上",
]


def ci95(p, n):
    """二项分布正态近似的 95% 置信区间半宽(百分点)。"""
    return round(196 * math.sqrt(p / 100 * (1 - p / 100) / n), 1) if n else None


def rel_video(run_id, path):
    """LeRobot 记录的是工作站绝对路径;同步后文件在 data/<id>/ 下 out/ 之后的相对位置。"""
    if "/out/" in path:
        rel = path.split("/out/", 1)[1]
    elif "/videos/" in path:  # 输出目录没有 out/ 这一层(如 ACT)
        rel = "videos/" + path.split("/videos/", 1)[1]
    else:
        rel = path
    return f"data/{run_id}/" + rel


def pick(videos, per_task):
    """每任务最多取 1 成功 + 1 失败;单任务环境(ACT/DP)则全部保留。"""
    if not per_task:
        return videos
    ok = [v for v in videos if v["success"]][:1]
    bad = [v for v in videos if not v["success"]][:1]
    return ok + bad


def load(run):
    d = ROOT / "data" / run["id"]
    info = json.loads((d / "eval_info.json").read_text())  # 缺文件直接报错,不静默留空
    tasks = info["per_task"]
    multi = len(tasks) > 1
    out = {"status": "done", "pc": round(info["overall"]["pc_success"], 1), "n": info["overall"]["n_episodes"],
           "tasks": [], "videos": []}
    for t in tasks:
        succ = t["metrics"]["successes"]
        tid = t.get("task_id", 0)
        name = LIBERO_SPATIAL_TASKS[tid] if multi and run["task"] == "LIBERO-Spatial" else run["task"]
        out["tasks"].append({"id": tid, "name": name, "ok": sum(succ), "n": len(succ)})
        vids = []
        if "videos" in t:  # OpenVLA 转换版:已给出相对路径与成败
            vids = [{"src": f"data/{run['id']}/{v['src']}", "ep": v["ep"], "success": v["success"]} for v in t["videos"]]
        else:
            for p in t["metrics"].get("video_paths", []):
                ep = int(re.search(r"eval_episode_(\d+)", p).group(1))
                rew = t["metrics"].get("sum_rewards", [None] * (ep + 1))[ep]
                vids.append({"src": rel_video(run["id"], p), "ep": ep, "success": bool(succ[ep]),
                             "reward": None if multi or rew is None else round(rew, 1)})
        for v in pick(vids, multi):
            v["task"] = name
            v.setdefault("reward", None)
            out["videos"].append(v)
    return out


rows = []
for run in RUNS:
    row = dict(run)
    row.update(load(run))
    if row.get("pc") is not None:
        row["ci"] = ci95(row["pc"], row["n"])
    if row.get("baseline_n") and "baseline_pm" not in row:
        row["baseline_ci"] = ci95(row["baseline_pc"], row["baseline_n"])
    rows.append(row)

# 视觉依赖测试(相机全涂黑)。OpenVLA 的录像保存的是送进模型的黑图,无观看价值,不收录视频。
BLACKOUT_RUNS = [
    {"id": "pi0_black_all", "model": "π0", "task": "LIBERO-Spatial"},
    {"id": "pi05_black_all", "model": "π0.5", "task": "LIBERO-Spatial"},
    {"id": "smol2_black_all", "model": "SmolVLA", "task": "LIBERO-Spatial"},
]
blackout = {"summary": json.loads((ROOT / "data" / "B_summary.json").read_text()),
            "runs": [dict(r, **load(r)) for r in BLACKOUT_RUNS]}

# 后续实验:末端轨迹、单路涂黑、温和扰动(缺文件直接报错)
def _json(name):
    return json.loads((ROOT / "data" / name).read_text())

def _n(run, first=None):
    """成功次数(first:只数每任务前几回合,用于从 500 回合评测里取同初始状态的 100 回合)。"""
    return sum(sum(t["metrics"]["successes"][:first]) for t in _json(f"{run}/eval_info.json")["per_task"])


# 温和扰动:加噪声 / 冻结画面(每组 100 回合,与正常、全涂黑同种子同初始状态)
PERTURB = [("pi0", "pi0_spatial_500", "pi0", "pi0_black_all"), ("pi0.5", "pi05_spatial_500", "pi05", "pi05_black_all"),
           ("SmolVLA", "smolvla2_spatial_500", "smol2", "smol2_black_all")]

followup = {
    "perturb": [{"model": m, "normal": _n(base, 10), "noise": _n(f"pert_{k}_noise"), "freeze": _n(f"pert_{k}_freeze"), "all_black": _n(black)}
                for m, base, k, black in PERTURB],
    "traj": _json("traj_analyze.json"),
    "cam": _json("cam_summary.json"),
}

(ROOT / "results.js").write_text("window.RESULTS = " + json.dumps(rows, ensure_ascii=False, indent=1) + ";\n"
                                 "window.LIBERO_TASKS = " + json.dumps(LIBERO_SPATIAL_TASKS, ensure_ascii=False) + ";\n"
                                 "window.BLACKOUT = " + json.dumps(blackout, ensure_ascii=False) + ";\n"
                                 "window.FOLLOWUP = " + json.dumps(followup, ensure_ascii=False) + ";\n")
print(f"wrote results.js: {len(rows)} runs, {sum(r['status'] == 'done' for r in rows)} done, "
      f"{sum(len(r.get('videos', [])) for r in rows)} videos")
