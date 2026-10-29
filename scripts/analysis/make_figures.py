"""从 dashboard/ 的评测汇总生成 results/*.csv 和 README 用的 SVG 图（只用标准库）。
英文图写到 media/，中文图写到 media/zh/。

用法（仓库根目录）：python3 dashboard/build.py && python3 scripts/analysis/make_figures.py
"""
import csv
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES, MEDIA = ROOT / "results", ROOT / "media"
FONT = "-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei','Noto Sans CJK SC',sans-serif"
INK, MUTED, GRID = "#1f2933", "#6b7280", "#e5e7eb"
BLUE, RED, ORANGE, VIOLET, ERR = "#2563eb", "#dc2626", "#ea580c", "#7c3aed", "#6b7280"
MODEL = {"pi0": "π0", "pi0.5": "π0.5"}

TXT = {
    "en": {
        "rep_title": "Public checkpoints: success rate in this repo vs. reference",
        "rep_ours": "This repo (500 episodes, 95% CI)", "rep_ref": "Reference", "rep_fail": "Not reproduced (intervals do not overlap)",
        "pert_title": "Success rate under camera perturbations (bar = mean, dots = two runs of 100 episodes)",
        "conds": ["Normal", "Gaussian noise", "Frozen first frame", "Agent-view black", "Wrist black", "All black"],
        "traj_title": "π0 end-effector paths, top view: 10 episodes per task, identical initial states",
        "traj_a": "Normal vs. normal re-run (noise floor)", "traj_b": "Normal vs. all cameras black",
        "traj_row": "Task {i}: bowl {name}. Blind π0 succeeds in {k} of 10 episodes.",
        "traj_task": {4: "in the top drawer of the cabinet", 7: "on the stove"},
        "traj_normal": "normal", "traj_rerun": "normal, re-run", "traj_black": "all cameras black", "traj_grasp": "dots = grasp points",
        "traj_start": "start", "traj_scale": "10 cm",
        "in_title": "What the policy receives, and what each experiment changes",
        "in_agent": "Agent-view camera", "in_wrist": "Wrist camera", "in_state": "Robot state", "in_lang": "Instruction",
        "in_policy": "Policy", "in_action": "Action",
        "in_img_note": "black / noise / frozen", "in_state_note": "unchanged",
        "in_lang_note": "unchanged", "in_sub_state": "end-effector pose and gripper opening", "in_sub_lang": "“pick up the black bowl …”",
        "sc_title": "One camera removed at test time (500 episodes per bar, 95% Wilson interval)",
        "sc_conds": ["Both cameras", "Wrist black", "Wrist dropped", "Wrist frozen at frame 1", "Agent view dropped"],
        "sc_note": "π0.5 wrist black: same 100 initial states run 5 times, 0/500",
        "op_title": "Official π0 vs. LeRobot π0 with cameras removed (95% Wilson interval)",
        "op_models": {"official": "Official π0 (OpenPI pipeline)", "lerobot": "LeRobot π0 v044"},
        "op_conds": ["Both cameras", "All black", "Both slots masked", "Both frozen at frame 1", "Wrist masked", "Agent view masked"],
        "op_n": "{k}/{n}",
    },
    "zh": {
        "rep_title": "公开权重复现：本机成功率 vs 基准",
        "rep_ours": "本机（500 回合，95% 置信区间）", "rep_ref": "基准", "rep_fail": "未复现（区间不重叠）",
        "pert_title": "扰动相机输入后的成功率（柱 = 平均，圆点 = 两次运行，各 100 回合）",
        "conds": ["正常", "加高斯噪声", "冻结首帧", "只涂主视角", "只涂腕部", "全涂黑"],
        "traj_title": "π0 末端执行器路线（俯视）：每个任务 10 个回合，初始状态相同",
        "traj_a": "正常 vs 正常重跑（噪声底线）", "traj_b": "正常 vs 相机全涂黑",
        "traj_row": "任务 {i}：碗在{name}。全涂黑时 10 回合成功 {k} 次。",
        "traj_task": {4: "木柜上层抽屉里", 7: "灶台上"},
        "traj_normal": "正常", "traj_rerun": "正常（重跑）", "traj_black": "相机全涂黑", "traj_grasp": "圆点 = 抓取点",
        "traj_start": "起点", "traj_scale": "10 cm",
        "in_title": "策略收到什么输入，各实验改了哪一项",
        "in_agent": "主视角相机", "in_wrist": "腕部相机", "in_state": "机械臂状态", "in_lang": "任务指令",
        "in_policy": "策略", "in_action": "动作",
        "in_img_note": "涂黑 / 加噪声 / 冻结", "in_state_note": "不改",
        "in_lang_note": "不改", "in_sub_state": "末端位姿与夹爪开合", "in_sub_lang": "“把黑碗拿起来放到……”",
        "sc_title": "测试时去掉一路相机（每根柱 500 回合，误差线为 Wilson 95% 区间）",
        "sc_conds": ["两路都给", "腕部涂黑", "去掉腕部", "腕部冻结在第 1 帧", "去掉主视角"],
        "sc_note": "π0.5 腕部涂黑：同一批 100 个初始状态跑 5 次，0/500",
        "op_title": "官方 π0 与 LeRobot π0 去掉相机后的成功率（误差线为 Wilson 95% 区间）",
        "op_models": {"official": "官方 π0（OpenPI 管线）", "lerobot": "LeRobot π0 v044"},
        "op_conds": ["两路都给", "全涂黑", "两路槽位都屏蔽", "两路冻结在第 1 帧", "只屏蔽腕部", "只屏蔽主视角"],
        "op_n": "{k}/{n}",
    },
}
COND_KEYS = ["normal", "noise", "freeze", "agent_black", "wrist_black", "all_black"]
COND_COL = ["#9ca3af", "#86efac", "#14b8a6", "#60a5fa", "#f59e0b", "#111827"]
# 单相机实验（docs/NOTES.md 的预先登记与结果）：dashboard/data/s500/<run>/，每个条件 500 回合，同一批初始状态
SC_RUNS = {"π0.5": {"both": "pi05_none", "wrist_dropped": "pi05_drop_wrist", "wrist_frozen": "pi05_freeze_wrist", "agent_dropped": "pi05_drop_agent"},
           "π0": {"both": "pi0_none", "both_rerun": "pi0_none_r2", "wrist_black": "pi0_wrist", "wrist_dropped": "pi0_drop_wrist",
                  "wrist_dropped_rerun": "pi0_drop_wrist_r2", "wrist_frozen": "pi0_freeze_wrist", "agent_dropped": "pi0_drop_agent"}}
SC_BARS = ["both", "wrist_black", "wrist_dropped", "wrist_frozen", "agent_dropped"]
SC_COL = ["#9ca3af", "#f59e0b", "#2563eb", "#14b8a6", "#7c3aed"]
# 官方 π0 对照（docs/NOTES.md 2026-10-28/29 的预先登记与结果）：路径相对 dashboard/data/，列表为多次运行合计
OP_RUNS = {"official": {"both": ["official_pi0/ojx_none"], "all_black": ["official_pi0/ojx_all"], "both_masked": ["official_pi0/ojx_drop_all"],
                        "both_frozen": ["official_pi0/ojx_freeze"], "wrist_masked": ["official_pi0/ojx_drop_wrist"],
                        "agent_masked": ["official_pi0/ojx_drop_agent"], "wrist_frozen": ["official_pi0/ojx_freeze_wrist"]},
           # 同一官方 π0 改用 360 渲染（与 LeRobot 一侧相同），排除分辨率这一混杂；不进图
           "official_360": {"both": ["official_pi0/ojx360_none"], "all_black": ["official_pi0/ojx360_all"],
                            "both_masked": ["official_pi0/ojx360_drop_all"]},
           "lerobot": {"both": ["s500/pi0_none"],
                       "all_black": ["pi0_black_all", "traj_pi0_black", "run2/pi0_black_all", "run2/traj_pi0_black", "run3/pi0_black_all"],
                       "both_masked": ["official_pi0/pi0_drop_all"], "both_frozen": ["pert_pi0_freeze", "run2/pert_pi0_freeze"],
                       "wrist_masked": ["s500/pi0_drop_wrist"], "agent_masked": ["s500/pi0_drop_agent"],
                       "wrist_frozen": ["s500/pi0_freeze_wrist"]},
           # LeRobot 转换版官方权重在 LeRobot 管线下的冒烟与三组对照（没跑通，留作记录，不进图）
           "conversion": {"smoke": ["official_pi0/opi0_smoke"], "diag_a": ["official_pi0/opi0_diag_a"],
                          "diag_b": ["official_pi0/opi0_diag_b"], "diag_c": ["official_pi0/opi0_diag_c"]}}
OP_BARS = ["both", "all_black", "both_masked", "both_frozen", "wrist_masked", "agent_masked"]
OP_COL = ["#9ca3af", "#111827", "#2563eb", "#14b8a6", "#f59e0b", "#7c3aed"]
OP_EEF_REF = "s500/pi0_none"  # 初始状态核对的参照：LeRobot π0 的 500 回合正常运行
TRAJ_TASKS = [4, 7]  # 轨迹图展示的任务：一个全涂黑仍成功的，一个全涂黑后失败的
PAIR_IDS = ["pi0_normal_vs_rerun", "pi0_all_black_vs_normal", "pi05_vs_pi0_normal"]  # 与 traj_analyze.json 里 pairs 的顺序一致
SRC_EN = {"ACT": "eval_info.json shipped in the Hugging Face repo (500 episodes)", "OpenVLA": "openvla README (3 seeds x 500 episodes)",
          "SmolVLA": "SmolVLA paper, Table 2 (10 episodes per task)", "π0.5": "OpenPI LIBERO README",
          "π0": "OpenPI LIBERO README at commit c015073f (π0 @30k)", "Diffusion Policy": "LeRobot model card (500 episodes)"}


def ci95(pc, n):
    """二项分布正态近似的 95% 置信区间半宽（百分点）；与 metrics.ci95 相同，这里重写一份以保持本脚本零依赖。"""
    return 196 * math.sqrt(pc / 100 * (1 - pc / 100) / n)


def wilson(k, n, z=1.96):
    """Wilson 95% 区间（百分数）。"""
    p, den = k / n, 1 + z * z / n
    c, hw = (p + z * z / (2 * n)) / den, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return 100 * (c - hw), 100 * (c + hw)


def mcnemar(b, c):
    """McNemar 精确检验（双侧）：b、c 为两种不一致的回合数。"""
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def load_single_camera():
    out = {}
    for model, conds in SC_RUNS.items():
        for cond, run in conds.items():
            d = ROOT / "dashboard" / "data" / "s500" / run
            per = sorted(json.loads((d / "eval_info.json").read_text())["per_task"], key=lambda t: t["task_id"])
            succ = [int(x) for t in per for x in t["metrics"]["successes"]]
            out[model, cond] = (succ, json.loads((d / "first_frame_hash.json").read_text()))
    return out


def single_camera_summary(sc):
    """每个条件：成功率、Wilson 区间，以及与同模型「两路都给」按初始状态配对的差值（95% 区间）和 McNemar p。"""
    rows = []
    for (model, cond), (s, _) in sc.items():
        n, k = len(s), sum(s)
        lo, hi = wilson(k, n)
        row = [model, cond, n, k, round(100 * k / n, 1), round(lo, 1), round(hi, 1)]
        if cond != "both":
            base = sc[model, "both"][0]
            x = [b - a for a, b in zip(base, s, strict=True)]
            m = sum(x) / n
            se = math.sqrt(sum((xi - m) ** 2 for xi in x) / (n - 1) / n)
            lost, gained = x.count(-1), x.count(1)
            row += [round(100 * m, 1), round(196 * se, 1), lost, gained, f"{mcnemar(lost, gained):.2g}"]
        else:
            row += ["", "", "", "", ""]
        rows.append(row)
    return rows


def fig_single_camera(summary, t):
    w, left, top, bh, gap = 760, 150, 70, 22, 6
    models = list(SC_RUNS)
    gh = len(SC_BARS) * (bh + gap) + 34
    h = top + gh * len(models) + 30
    pw = w - left - 70
    x = lambda v: left + pw * v / 100
    by = {(r[0], r[1]): r for r in summary}
    out = [title(t["sc_title"])]
    for v in range(0, 101, 25):
        out.append(f'<line x1="{x(v):.1f}" y1="{top - 8}" x2="{x(v):.1f}" y2="{h - 30}" stroke="{GRID}"/>')
        out.append(f'<text x="{x(v):.1f}" y="{h - 12}" text-anchor="middle" fill="{MUTED}">{v}%</text>')
    for g, model in enumerate(models):
        y0 = top + g * gh
        out.append(f'<text x="20" y="{y0 + 6}" font-size="14" font-weight="600">{model}</text>')
        for i, (cond, col, lab) in enumerate(zip(SC_BARS, SC_COL, t["sc_conds"], strict=True)):
            y = y0 + 16 + i * (bh + gap)
            out.append(f'<text x="{left - 10}" y="{y + bh / 2 + 4:.1f}" text-anchor="end">{lab}</text>')
            r = by.get((model, cond))
            if r is None:  # π0.5 腕部涂黑没有在这一轮重跑
                out.append(f'<text x="{x(0) + 6:.1f}" y="{y + bh / 2 + 4:.1f}" font-size="12" fill="{MUTED}">{t["sc_note"]}</text>')
                continue
            pc, lo, hi = r[4], r[5], r[6]
            out.append(f'<rect x="{x(0):.1f}" y="{y}" width="{max(x(pc) - x(0), 1.5):.1f}" height="{bh}" rx="2" fill="{col}"/>')
            out.append(f'<line x1="{x(lo):.1f}" y1="{y + bh / 2}" x2="{x(hi):.1f}" y2="{y + bh / 2}" stroke="{INK}" stroke-width="1.4"/>')
            for e in (lo, hi):
                out.append(f'<line x1="{x(e):.1f}" y1="{y + 6}" x2="{x(e):.1f}" y2="{y + bh - 6}" stroke="{INK}" stroke-width="1.4"/>')
            out.append(f'<text x="{x(hi) + 6:.1f}" y="{y + bh / 2 + 4:.1f}" font-size="12" font-weight="600">{pc:.1f}</text>')
    return svg(w, h, out)


def _succ(run):
    per = sorted(json.loads((ROOT / "dashboard" / "data" / run / "eval_info.json").read_text())["per_task"], key=lambda t: t["task_id"])
    return [int(x) for t in per for x in t["metrics"]["successes"]]


def official_pi0_summary():
    """每个条件：回合数、成功数、Wilson 区间；官方运行另算第 1 步末端位置与参照运行同一初始状态的最大差（cm）。"""
    data = ROOT / "dashboard" / "data"
    ref = json.loads((data / OP_EEF_REF / "first_eef.json").read_text())
    rows = []
    for side, conds in OP_RUNS.items():
        for cond, runs in conds.items():
            succ = [x for r in runs for x in _succ(r)]
            n, k = len(succ), sum(succ)
            lo, hi = wilson(k, n)
            eef = ""
            if side.startswith("official"):
                e = json.loads((data / runs[0] / "first_eef.json").read_text())
                per = len(e) // 10  # 每任务回合数；参照每任务 50 回合，取前 per 个
                assert per * 10 == len(e) and len(ref) == 500
                eef = round(100 * max(abs(a - b) for i, p in enumerate(e) for a, b in zip(p, ref[i // per * 50 + i % per], strict=True)), 4)
            rows.append([side, cond, len(runs), n, k, round(100 * k / n, 1), round(max(lo, 0.0), 1), round(hi, 1), eef])
    return rows


def fig_official_pi0(summary, t):
    w, left, top, bh, gap = 760, 160, 70, 20, 5
    gh = len(OP_BARS) * (bh + gap) + 34
    h = top + gh * 2 + 30
    pw = w - left - 90
    x = lambda v: left + pw * v / 100
    by = {(r[0], r[1]): r for r in summary}
    out = [title(t["op_title"])]
    for v in range(0, 101, 25):
        out.append(f'<line x1="{x(v):.1f}" y1="{top - 8}" x2="{x(v):.1f}" y2="{h - 30}" stroke="{GRID}"/>')
        out.append(f'<text x="{x(v):.1f}" y="{h - 12}" text-anchor="middle" fill="{MUTED}">{v}%</text>')
    for g, side in enumerate(("official", "lerobot")):
        y0 = top + g * gh
        out.append(f'<text x="20" y="{y0 + 6}" font-size="14" font-weight="600">{t["op_models"][side]}</text>')
        for i, (cond, col, lab) in enumerate(zip(OP_BARS, OP_COL, t["op_conds"], strict=True)):
            y = y0 + 16 + i * (bh + gap)
            _, _, _, n, k, pc, lo, hi, _ = by[side, cond]
            out.append(f'<text x="{left - 10}" y="{y + bh / 2 + 4:.1f}" text-anchor="end">{lab}</text>')
            out.append(f'<rect x="{x(0):.1f}" y="{y}" width="{max(x(pc) - x(0), 1.5):.1f}" height="{bh}" rx="2" fill="{col}"/>')
            out.append(f'<line x1="{x(lo):.1f}" y1="{y + bh / 2}" x2="{x(hi):.1f}" y2="{y + bh / 2}" stroke="{INK}" stroke-width="1.4"/>')
            for e in (lo, hi):
                out.append(f'<line x1="{x(e):.1f}" y1="{y + 5}" x2="{x(e):.1f}" y2="{y + bh - 5}" stroke="{INK}" stroke-width="1.4"/>')
            out.append(f'<text x="{x(hi) + 6:.1f}" y="{y + bh / 2 + 4:.1f}" font-size="12"><tspan font-weight="600">{pc:.1f}</tspan>'
                       f'<tspan fill="{MUTED}"> ({t["op_n"].format(k=k, n=n)})</tspan></text>')
    return svg(w, h, out)


def load_dashboard():
    s = (ROOT / "dashboard" / "results.js").read_text()
    return {m.group(1): json.loads(m.group(2)) for m in re.finditer(r"window\.(\w+) = (.*?);\n(?=window\.|\Z)", s, re.S)}


def write_csv(name, header, rows):
    with open(RES / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" '
            f'font-family="{FONT}" font-size="13" fill="{INK}">\n'
            f'<rect width="{w:.0f}" height="{h:.0f}" rx="8" fill="#ffffff"/>\n' + "\n".join(body) + "\n</svg>\n")


def title(t):
    return f'<text x="20" y="28" font-size="16" font-weight="600">{t}</text>'


def tw(s, size=13):
    """粗略估计文字宽度（像素），用于排图例。"""
    return sum(size * (0.56 if c.isascii() else 1.0) for c in s)


def reproduced(r):
    """本机区间与基准区间（没有则取基准点）是否重叠。"""
    b = r.get("baseline_pm") or r.get("baseline_ci") or 0
    return abs(r["pc"] - r["baseline_pc"]) <= r["ci"] + b


def fig_reproduction(rows, t):
    w, left, right, top, rh = 760, 190, 40, 64, 44
    h = top + rh * len(rows) + 46
    x = lambda v: left + (w - left - right) * (v - 50) / 50  # 横轴 50–100%
    lx2 = 38 + tw(t["rep_ours"]) + 26
    lx3 = lx2 + 14 + tw(t["rep_ref"]) + 26
    out = [title(t["rep_title"]),
           f'<circle cx="26" cy="46" r="5" fill="{BLUE}"/><text x="38" y="50" fill="{MUTED}">{t["rep_ours"]}</text>',
           f'<path d="M{lx2:.0f} 40 l6 6 l-6 6 l-6 -6 z" fill="none" stroke="{INK}" stroke-width="1.6"/>'
           f'<text x="{lx2 + 14:.0f}" y="50" fill="{MUTED}">{t["rep_ref"]}</text>'
]
    if not all(reproduced(r) for r in rows):
        out.append(f'<circle cx="{lx3:.0f}" cy="46" r="5" fill="{RED}"/><text x="{lx3 + 12:.0f}" y="50" fill="{MUTED}">{t["rep_fail"]}</text>')
    for v in range(50, 101, 10):
        out.append(f'<line x1="{x(v):.1f}" y1="{top}" x2="{x(v):.1f}" y2="{h - 40}" stroke="{GRID}"/>')
        out.append(f'<text x="{x(v):.1f}" y="{h - 22}" text-anchor="middle" fill="{MUTED}">{v}%</text>')
    for i, r in enumerate(rows):
        y = top + rh * i + rh / 2
        c = BLUE if reproduced(r) else RED
        out.append(f'<text x="{left - 14}" y="{y - 2:.1f}" text-anchor="end" font-weight="600">{r["model"]}</text>')
        out.append(f'<text x="{left - 14}" y="{y + 13:.1f}" text-anchor="end" font-size="11" fill="{MUTED}">{r["task"]}</text>')
        out.append(f'<line x1="{x(r["pc"] - r["ci"]):.1f}" y1="{y}" x2="{x(r["pc"] + r["ci"]):.1f}" y2="{y}" '
                   f'stroke="{c}" stroke-width="3" stroke-linecap="round" opacity="0.45"/>')
        out.append(f'<circle cx="{x(r["pc"]):.1f}" cy="{y}" r="5.5" fill="{c}"/>')
        bx = x(r["baseline_pc"])
        out.append(f'<path d="M{bx:.1f} {y - 7} l7 7 l-7 7 l-7 -7 z" fill="none" stroke="{INK}" stroke-width="1.6"/>')
        out.append(f'<text x="{x(r["pc"]):.1f}" y="{y - 11:.1f}" text-anchor="middle" font-size="12" fill="{c}" font-weight="600">{r["pc"]:.1f}</text>')
        if abs(r["pc"] - r["baseline_pc"]) > 6:  # 离得远才单独标基准值，避免重叠
            out.append(f'<text x="{bx:.1f}" y="{y - 11:.1f}" text-anchor="middle" font-size="12">{r["baseline_pc"]:.1f}</text>')
    return svg(w, h, out)


def fig_perturbations(rows, t):
    w, h, left, top, bot = 760, 350, 56, 92, 44
    ph, gw, bw, gap = h - top - bot, (w - left - 30) / len(rows), 26, 5
    y = lambda v: top + ph * (1 - v / 100)
    out = [title(t["pert_title"])]
    lx = 20
    for lab, col in zip(t["conds"], COND_COL, strict=True):
        out.append(f'<rect x="{lx:.0f}" y="42" width="12" height="12" rx="2" fill="{col}"/><text x="{lx + 17:.0f}" y="53" fill="{MUTED}">{lab}</text>')
        lx += 17 + tw(lab) + 18
    for v in range(0, 101, 25):
        out.append(f'<line x1="{left}" y1="{y(v):.1f}" x2="{w - 30}" y2="{y(v):.1f}" stroke="{GRID}"/>')
        out.append(f'<text x="{left - 8}" y="{y(v) + 4:.1f}" text-anchor="end" fill="{MUTED}">{v}%</text>')
    for g, m in enumerate(rows):
        x0 = left + gw * g + (gw - bw * 6 - gap * 5) / 2
        for i, (key, col) in enumerate(zip(COND_KEYS, COND_COL, strict=True)):
            runs = [r for r in m[key] if r is not None]  # 每个条件一到两次运行
            v, bx = sum(runs) / len(runs), x0 + i * (bw + gap)
            hi, cx = max(runs), bx + bw / 2
            out.append(f'<rect x="{bx:.1f}" y="{y(max(v, 0.8)):.1f}" width="{bw}" height="{ph - (y(max(v, 0.8)) - top):.1f}" rx="2" fill="{col}"/>')
            if len(runs) > 1:
                for j, r in enumerate(runs):
                    out.append(f'<circle cx="{cx + (j - 0.5) * 9:.1f}" cy="{y(r):.1f}" r="3.2" fill="#fff" stroke="#111827" stroke-width="1.3"/>')
            out.append(f'<text x="{cx:.1f}" y="{y(hi) - 8:.1f}" text-anchor="middle" font-size="12" font-weight="600">{v:g}</text>')
        out.append(f'<text x="{left + gw * (g + 0.5):.1f}" y="{h - 16}" text-anchor="middle" font-weight="600">{MODEL.get(m["model"], m["model"])}</text>')
    return svg(w, h, out)


def fig_trajectory(trajs, t):
    """每个任务一行、两幅俯视图：左 = 正常两次（噪声底线），右 = 正常 vs 全涂黑。坐标为机器人基座系 XY(cm)，各行同一比例尺。"""
    pw, pad, top = 340, 26, 104
    box = []
    for tr in trajs:
        pts = [p for eps in tr["runs"].values() for e in eps for p in e["xy"]]
        box.append((min(p[0] for p in pts) - 2, max(p[0] for p in pts) + 2, min(p[1] for p in pts) - 2, max(p[1] for p in pts) + 2))
    s = (pw - 20) / max(b[3] - b[2] for b in box)  # 画面横向 = 机器人 Y，纵向 = 机器人 X
    w = pad * 2 + pw * 2 + 28
    out = [title(t["traj_title"])]
    lx = pad
    for lab, col in ((t["traj_normal"], BLUE), (t["traj_rerun"], VIOLET), (t["traj_black"], ORANGE)):
        out.append(f'<line x1="{lx:.0f}" y1="46" x2="{lx + 18:.0f}" y2="46" stroke="{col}" stroke-width="2.5"/><text x="{lx + 23:.0f}" y="50" fill="{MUTED}">{lab}</text>')
        lx += 23 + tw(lab) + 18
    out.append(f'<text x="{lx:.0f}" y="50" fill="{MUTED}">{t["traj_grasp"]}</text>')
    for ox, name in ((pad, t["traj_a"]), (pad + pw + 28, t["traj_b"])):
        out.append(f'<text x="{ox}" y="76" font-weight="600">{name}</text>')

    def panel(runs, b, ox, oy, phh, a, c, ca, cc):
        X = lambda p: ox + 10 + (pw - 20 - s * (b[3] - b[2])) / 2 + s * (p[1] - b[2])
        Y = lambda p: oy + 10 + s * (p[0] - b[0])
        o = [f'<rect x="{ox}" y="{oy:.1f}" width="{pw}" height="{phh:.1f}" rx="6" fill="#f9fafb" stroke="{GRID}"/>']
        for run, col in ((a, ca), (c, cc)):
            for e in runs[run]:
                d = " ".join(f"{X(p):.1f},{Y(p):.1f}" for p in e["xy"])
                o.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="1.3" opacity="0.55" stroke-linejoin="round"/>')
        for run, col in ((a, ca), (c, cc)):
            for e in runs[run]:
                if e["grasp"]:
                    o.append(f'<circle cx="{X(e["grasp"]):.1f}" cy="{Y(e["grasp"]):.1f}" r="3.6" fill="{col}" stroke="#ffffff" stroke-width="1"/>')
        st = runs[a][0]["xy"][0]
        o.append(f'<circle cx="{X(st):.1f}" cy="{Y(st):.1f}" r="4.5" fill="none" stroke="{INK}" stroke-width="1.5"/>'
                 f'<text x="{X(st):.1f}" y="{Y(st) - 9:.1f}" text-anchor="middle" font-size="11" fill="{INK}">{t["traj_start"]}</text>')
        bx, by = ox + pw - 14 - 10 * s, oy + phh - 12
        o.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{bx + 10 * s:.1f}" y2="{by:.1f}" stroke="{INK}" stroke-width="2"/>'
                 f'<text x="{bx + 5 * s:.1f}" y="{by - 5:.1f}" text-anchor="middle" font-size="11" fill="{MUTED}">{t["traj_scale"]}</text>')
        return o

    oy = top
    for tr, b in zip(trajs, box, strict=True):
        runs, phh = tr["runs"], s * (b[1] - b[0]) + 20
        k = sum(e["success"] for e in runs["traj_pi0_black"])
        out.append(f'<text x="{pad}" y="{oy - 8:.1f}" font-size="12" fill="{MUTED}">{t["traj_row"].format(i=tr["task"], name=t["traj_task"][tr["task"]], k=k)}</text>')
        out += panel(runs, b, pad, oy, phh, "traj_pi0_normal", "traj_pi0_normal2", BLUE, VIOLET)
        out += panel(runs, b, pad + pw + 28, oy, phh, "traj_pi0_normal", "traj_pi0_black", BLUE, ORANGE)
        oy += phh + 34
    return svg(w, oy - 16, out)


def fig_inputs(t):
    w, h, bx, bw, bh = 760, 300, 30, 330, 46
    rows = [("in_agent", None, "in_img_note", ORANGE), ("in_wrist", None, "in_img_note", ORANGE),
            ("in_state", "in_sub_state", "in_state_note", MUTED), ("in_lang", "in_sub_lang", "in_lang_note", MUTED)]
    px, py, pw, ph = 500, 106, 120, 110
    out = [title(t["in_title"]),
           '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
           f'<path d="M0 0 L10 5 L0 10 z" fill="{MUTED}"/></marker></defs>']
    for i, (k, sub, note, col) in enumerate(rows):
        y = 50 + i * 60
        label = t[k] + (f'<tspan font-weight="400" font-size="11" fill="{MUTED}">  {t[sub]}</tspan>' if sub else "")
        out.append(f'<rect x="{bx}" y="{y}" width="{bw}" height="{bh}" rx="6" fill="#f9fafb" stroke="{GRID}" stroke-width="1.5"/>')
        out.append(f'<text x="{bx + 14}" y="{y + 19}" font-weight="600">{label}</text>')
        out.append(f'<text x="{bx + 14}" y="{y + 36}" font-size="12" fill="{col}" font-weight="600">{t[note]}</text>')
        out.append(f'<path d="M{bx + bw} {y + bh / 2} L{px - 6} {py + 22 + i * 22}" fill="none" stroke="{MUTED}" stroke-width="1.3" marker-end="url(#a)"/>')
    out.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="8" fill="{BLUE}"/>'
               f'<text x="{px + pw / 2}" y="{py + ph / 2 + 5}" text-anchor="middle" fill="#ffffff" font-size="15" font-weight="600">{t["in_policy"]}</text>')
    out.append(f'<path d="M{px + pw} {py + ph / 2} L{px + pw + 44} {py + ph / 2}" stroke="{MUTED}" stroke-width="1.3" marker-end="url(#a)"/>')
    out.append(f'<text x="{px + pw + 52}" y="{py + ph / 2 + 5}" font-weight="600">{t["in_action"]}</text>')
    return svg(w, h, out)


if __name__ == "__main__":
    RES.mkdir(exist_ok=True)
    (MEDIA / "zh").mkdir(parents=True, exist_ok=True)
    d = load_dashboard()
    runs = [r for r in d["RESULTS"] if r["status"] == "done"]
    fu = d["FOLLOWUP"]
    write_csv("reproduction.csv", ["model", "task", "checkpoint", "episodes", "success_pc", "ci95", "baseline_pc", "baseline_source", "reproduced"],
              [[r["model"], r["task"], r["checkpoint"], r["n"], r["pc"], r["ci"], r["baseline_pc"], SRC_EN[r["model"]], int(reproduced(r))] for r in runs])
    write_csv("blackout_per_task.csv", ["model", "condition"] + [f"task{i}" for i in range(10)] + ["total"],
              [[MODEL.get(m["model"], m["model"]), c] + m[c] + [sum(m[c])] for m in d["BLACKOUT"]["summary"] for c in ("normal", "black")])
    cam = {m["model"]: m for m in fu["cam"]}
    run1 = [{**p, "agent_black": cam[p["model"]]["agent_black"], "wrist_black": cam[p["model"]]["wrist_black"]} for p in fu["perturb"]]
    write_csv("perturbations.csv", ["model", "run"] + COND_KEYS,
              [[MODEL.get(m["model"], m["model"]), n] + ["" if m[k] is None else m[k] for k in COND_KEYS]
               for a, b in zip(run1, fu["perturb2"], strict=True) for n, m in ((1, a), (2, b))])
    pert = [{"model": a["model"], **{k: [a[k], b[k]] for k in COND_KEYS}} for a, b in zip(run1, fu["perturb2"], strict=True)]
    tasks = [f"task{i}" for i in range(10)]
    rows = []
    for n, tj in ((1, fu["traj"]), (2, fu["traj2"])):
        succ = tj["successes_by_task"]["traj_pi0_black"]
        rows.append([n, "successes", "pi0_all_black"] + succ + [sum(succ)])
        for metric, by, mean in (("path_dtw_cm", "dtw_by_task", "dtw_mean"), ("grasp_distance_cm", "grasp_dist_by_task", "grasp_dist_mean")):
            rows += [[n, metric, pid] + [round(x, 2) for x in v[by]] + [round(v[mean], 2)] for pid, v in zip(PAIR_IDS, tj["pairs"].values(), strict=True)]
    write_csv("trajectory.csv", ["run", "metric", "pair"] + tasks + ["all"], rows)
    sc = load_single_camera()
    write_csv("single_camera.csv", ["model", "condition", "task", "episode", "success", "first_frame_hash"],
              [[m, c, i // 50, i % 50, s, h] for (m, c), (succ, hs) in sc.items() for i, (s, h) in enumerate(zip(succ, hs, strict=True))])
    sc_sum = single_camera_summary(sc)
    write_csv("single_camera_summary.csv", ["model", "condition", "episodes", "successes", "success_pc", "wilson_lo", "wilson_hi",
                                            "paired_diff_pp", "diff_ci95_pp", "lost", "gained", "mcnemar_p"], sc_sum)
    op_sum = official_pi0_summary()
    write_csv("official_pi0_summary.csv", ["side", "condition", "runs", "episodes", "successes", "success_pc", "wilson_lo", "wilson_hi",
                                           "first_eef_max_diff_cm"], op_sum)
    traj = [json.loads((RES / f"trajectories_task{i}.json").read_text()) for i in TRAJ_TASKS]
    for lang, out in (("en", MEDIA), ("zh", MEDIA / "zh")):
        t = TXT[lang]
        (out / "reproduction.svg").write_text(fig_reproduction(runs, t))
        (out / "perturbations.svg").write_text(fig_perturbations(pert, t))
        (out / "trajectory.svg").write_text(fig_trajectory(traj, t))
        (out / "inputs.svg").write_text(fig_inputs(t))
        (out / "single_camera.svg").write_text(fig_single_camera(sc_sum, t))
        (out / "official_pi0.svg").write_text(fig_official_pi0(op_sum, t))
    print(f"wrote {len(list(RES.glob('*.csv')))} csv -> results/, 6 svg -> media/ and media/zh/")
