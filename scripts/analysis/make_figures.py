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
        "rep_ours": "This repo (500 episodes, 95% CI)", "rep_ref": "Reference", "rep_fail": "Repo criterion not met",
        "pert_title": "Success rate under camera perturbations (bar = mean, dots = two runs of 100 episodes)",
        "conds": ["Normal", "Both noise", "Both frozen", "Agent-view black", "Wrist black", "All black"],
        "traj_title": "π0 end-effector paths, top view: 10 episodes per task, identical initial states",
        "traj_a": "Normal vs. normal re-run", "traj_b": "Normal vs. all cameras black",
        "traj_row": "Task {i}: bowl {name}. Blind π0 succeeds in {k} of 10 episodes.",
        "traj_task": {4: "in the top drawer of the cabinet", 7: "on the stove"},
        "traj_normal": "normal", "traj_rerun": "normal, re-run", "traj_black": "all cameras black", "traj_grasp": "dots = grasp points",
        "traj_start": "start", "traj_scale": "10 cm",
        "in_title": "What the policy receives, and what each experiment changes",
        "in_agent": "Agent-view camera", "in_wrist": "Wrist camera", "in_state": "Robot state", "in_lang": "Instruction",
        "in_policy": "Policy", "in_action": "Action",
        "in_img_note": "black / noise / frozen", "in_state_note": "unchanged",
        "in_lang_note": "unchanged", "in_sub_state": "end-effector pose and gripper opening", "in_sub_lang": "“pick up the black bowl …”",
        "sc_title": "Wrist-treatment study (π0 / π0.5 v044); agent masking is supplementary",
        "sc_conds": ["Both cameras", "Wrist black", "Wrist dropped", "Wrist frozen at frame 1", "Agent view dropped"],
        "sc_note": "π0.5 wrist black: same 100 initial states run 5 times, 0/500",
        "op_title": "Official π0 control: same 100 initial states per point; repeats shown separately",
        "op_models": {"official": "Official π0 (OpenPI pipeline)", "lerobot": "LeRobot π0 v044"},
        "op_conds": ["Both cameras", "All black", "Both slots masked", "Both frozen at frame 1", "Wrist masked", "Agent view masked"],
        "op_n": "{k}/{n}",
        "rp_title": "Fixed-action replay: source-state selection and cross-replay",
        "rp_bars": ["Best fixed sequence (on the other 9 states)", "All cross-replays"],
        "rp_band": "LeRobot π0 all black, 53–56%",
        "rp_null": "Best of k if every sequence scored {p:.1f}%: {v:.1f}%",
        "rp_lr": "LeRobot π0 all black, same task (mean of 5 runs)",
        "rp_all": "Mean",
        "rp_task": "Task {i}",
    },
    "zh": {
        "rep_title": "公开权重对照：本机成功率 vs 参考值",
        "rep_ours": "本机（500 回合，95% 置信区间）", "rep_ref": "参考值", "rep_fail": "未达本项目判据（范围不重叠）",
        "pert_title": "扰动相机输入后的成功率（柱 = 平均，圆点 = 两次运行，各 100 回合）",
        "conds": ["正常", "双路加噪声", "双路冻结首帧", "只涂主视角", "只涂腕部", "全涂黑"],
        "traj_title": "π0 末端执行器路线（俯视）：每个任务 10 个回合，初始状态相同",
        "traj_a": "正常 vs 正常重跑", "traj_b": "正常 vs 相机全涂黑",
        "traj_row": "任务 {i}：碗在{name}。全涂黑时 10 回合成功 {k} 次。",
        "traj_task": {4: "木柜上层抽屉里", 7: "灶台上"},
        "traj_normal": "正常", "traj_rerun": "正常（重跑）", "traj_black": "相机全涂黑", "traj_grasp": "圆点 = 抓取点",
        "traj_start": "起点", "traj_scale": "10 cm",
        "in_title": "策略收到什么输入，各实验改了哪一项",
        "in_agent": "主视角相机", "in_wrist": "腕部相机", "in_state": "机械臂状态", "in_lang": "任务指令",
        "in_policy": "策略", "in_action": "动作",
        "in_img_note": "涂黑 / 加噪声 / 冻结", "in_state_note": "不改",
        "in_lang_note": "不改", "in_sub_state": "末端位姿与夹爪开合", "in_sub_lang": "“把黑碗拿起来放到……”",
        "sc_title": "腕部单因素主实验（π0／π0.5 v044）；主视角屏蔽单列为附加条件",
        "sc_conds": ["两路都给", "腕部涂黑", "去掉腕部", "腕部冻结在第 1 帧", "去掉主视角"],
        "sc_note": "π0.5 腕部涂黑：同一批 100 个初始状态跑 5 次，0/500",
        "op_title": "官方 π0 对照：每个点为同100初态；重复逐次展示，不合并区间",
        "op_models": {"official": "官方 π0（OpenPI 管线）", "lerobot": "LeRobot π0 v044"},
        "op_conds": ["两路都给", "全涂黑", "两路槽位都屏蔽", "两路冻结在第 1 帧", "只屏蔽腕部", "只屏蔽主视角"],
        "op_n": "{k}/{n}",
        "rp_title": "固定动作回放：来源状态上的选择与交叉回放",
        "rp_bars": ["最好的一套固定动作（在另外 9 个状态上）", "全部交叉回放"],
        "rp_band": "LeRobot π0 全涂黑 53–56%",
        "rp_null": "若每套都只有 {p:.1f}%，挑最好一套的期望：{v:.1f}%",
        "rp_lr": "LeRobot π0 同一任务全涂黑（5 次平均）",
        "rp_all": "平均",
        "rp_task": "任务 {i}",
    },
}
COND_KEYS = ["normal", "noise", "freeze", "agent_black", "wrist_black", "all_black"]
COND_COL = ["#9ca3af", "#86efac", "#14b8a6", "#60a5fa", "#f59e0b", "#111827"]
# 单相机实验（docs/NOTES.md 的预先登记与结果）：dashboard/data/s500/<run>/，每个条件 500 回合，同一批初始状态
SC_RUNS = {"π0.5": {"both": "pi05_none", "wrist_dropped": "pi05_drop_wrist", "wrist_frozen": "pi05_freeze_wrist", "agent_dropped": "pi05_drop_agent"},
           "π0": {"both": "pi0_none", "both_rerun": "pi0_none_r2", "wrist_black": "pi0_wrist", "wrist_dropped": "pi0_drop_wrist",
                  "wrist_dropped_rerun": "pi0_drop_wrist_r2", "wrist_frozen": "pi0_freeze_wrist", "agent_dropped": "pi0_drop_agent"}}
SC_BARS = ["both", "wrist_black", "wrist_dropped", "wrist_frozen", "agent_dropped"]
SC_COL = ["#9ca3af", "#3c73ac", "#3c73ac", "#3c73ac", "#7d8da1"]
# 官方 π0 对照（docs/NOTES.md 2026-10-28/29 的预先登记与结果）：路径相对 dashboard/data/，列表为多次运行合计
OP_RUNS = {"official": {"both": ["official_pi0/ojx_none"], "all_black": ["official_pi0/ojx_all"], "both_masked": ["official_pi0/ojx_drop_all"],
                        "both_frozen": ["official_pi0/ojx_freeze"], "wrist_masked": ["official_pi0/ojx_drop_wrist"],
                        "agent_masked": ["official_pi0/ojx_drop_agent"], "wrist_frozen": ["official_pi0/ojx_freeze_wrist"]},
           # 同一官方 π0 改用360渲染，核对本次分辨率变更下的结果；不进图
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
RP_RUN = "official_pi0/ojx360_replay"  # 开环回放的动作来源（官方 π0，360 渲染，正常条件）与回放结果
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
    gh = len(SC_BARS) * (bh + gap) + 64
    h = top + gh * len(models) + 30
    pw = w - left - 70
    x = lambda v: left + pw * v / 100
    by = {(r[0], r[1]): r for r in summary}
    out = [title(t["sc_title"])]
    note = ("Agent view live in main conditions; new runs500 each; bars: Wilson95%; historical wrist-black noted separately."
            if t is TXT["en"] else "主实验中主视角正常；新运行每条件500回合，横线为Wilson95%区间；历史腕部黑图单独注记。")
    out.append(f'<text x="20" y="45" font-size="11" fill="{MUTED}">{note}</text>')
    for v in range(0, 101, 25):
        out.append(f'<line x1="{x(v):.1f}" y1="{top - 8}" x2="{x(v):.1f}" y2="{h - 30}" stroke="{GRID}"/>')
        out.append(f'<text x="{x(v):.1f}" y="{h - 12}" text-anchor="middle" fill="{MUTED}">{v}%</text>')
    for g, model in enumerate(models):
        y0 = top + g * gh
        out.append(f'<text x="20" y="{y0 + 6}" font-size="14" font-weight="600">LeRobot {model} v044</text>')
        for i, (cond, col, lab) in enumerate(zip(SC_BARS, SC_COL, t["sc_conds"], strict=True)):
            y = y0 + 16 + i * (bh + gap) + (26 if cond == "agent_dropped" else 0)
            if cond == "agent_dropped":
                label = "Supplementary: wrist remains live" if t is TXT["en"] else "附加条件：腕部正常更新"
                out.append(f'<line x1="20" x2="{w-20}" y1="{y-20}" y2="{y-20}" stroke="{GRID}" stroke-dasharray="4 4"/>')
                out.append(f'<text x="20" y="{y-5}" font-size="11" fill="{MUTED}">{label}</text>')
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
            # Repeated executions reuse the same initial states; do not treat them as independent Bernoulli samples.
            lo, hi = wilson(k, n) if len(runs) == 1 else (None, None)
            eef = ""
            if side.startswith("official"):
                e = json.loads((data / runs[0] / "first_eef.json").read_text())
                per = len(e) // 10  # 每任务回合数；参照每任务 50 回合，取前 per 个
                assert per * 10 == len(e) and len(ref) == 500
                eef = round(100 * max(abs(a - b) for i, p in enumerate(e) for a, b in zip(p, ref[i // per * 50 + i % per], strict=True)), 4)
            rows.append([side, cond, len(runs), n, k, round(100 * k / n, 1), round(max(lo, 0.0), 1) if lo is not None else "", round(hi, 1) if hi is not None else "", eef])
    return rows


def replay_summary():
    """开环回放基线（docs/NOTES.md 2026-10-29 事前记录）：每任务自回放、全部交叉回放、最好的一套固定动作，以及物体位置的变化范围（cm）。
    另算两项更正用的对照（docs/NOTES.md 2026-10-29 更正）：每套真实成功率都等于全部交叉回放合计时，从 k 套里挑最好一套的期望成功率
    （k 为该任务成功来源数，每套在 9 个状态上二项分布，精确计算）；LeRobot π0 同一任务全涂黑的成功率（5 次运行平均）。"""
    r = json.loads((ROOT / "dashboard" / "data" / RP_RUN / "replay.json").read_text())
    pool = sum(sum(d.values()) for t in r["tasks"] for d in t["cross"].values()) / sum(len(d) for t in r["tasks"] for d in t["cross"].values())
    cdf = lambda m: sum(math.comb(9, i) * pool ** i * (1 - pool) ** (9 - i) for i in range(m + 1))
    black = [_succ(run) for run in OP_RUNS["lerobot"]["all_black"]]
    rows, null = [], []
    for t in r["tasks"]:
        cross = {e: (sum(d.values()), len(d)) for e, d in t["cross"].items()}
        best = max(cross, key=lambda e: cross[e][0])
        null.append(100 * sum(1 - cdf(m - 1) ** len(cross) for m in range(1, 10)) / 9)
        span = [100 * (max(o[k][a] for o in t["objects"]) - min(o[k][a] for o in t["objects"])) for k in t["objects"][0] for a in (0, 1)]
        rows.append([t["task"], sum(t["source_success"]), sum(t["self"].values()), len(t["self"]),
                     sum(k for k, _ in cross.values()), sum(n for _, n in cross.values()), int(best), cross[best][0], cross[best][1],
                     round(max(span), 1), round(null[-1], 1),
                     round(100 * sum(sum(b[t["task"] * 10:(t["task"] + 1) * 10]) for b in black) / (10 * len(black)), 1)])
    tot = [sum(c) for c in list(zip(*rows, strict=True))[1:6]]
    best_pc = sum(r[7] / r[8] for r in rows) / len(rows)
    rows.append(["all", *tot, "", round(100 * best_pc, 1), "", max(r[9] for r in rows),
                 round(sum(null) / len(null), 1), round(sum(r[11] for r in rows) / len(rows), 1)])
    return rows


def fig_replay(rows, t):
    w, left, top, bh, gap = 760, 90, 112, 11, 9
    tasks = rows[:-1]
    h = top + (len(tasks) + 1) * (2 * bh + gap) + 58
    pw = w - left - 70
    x = lambda v: left + pw * v / 100
    out = [title(t["rp_title"])]
    out.append(f'<rect x="{x(53):.1f}" y="{top - 10}" width="{x(56) - x(53):.1f}" height="{h - top - 22}" fill="#fde68a"/>')
    out.append(f'<text x="{x(54.5):.1f}" y="{top - 14}" text-anchor="middle" font-size="11" fill="{MUTED}">{t["rp_band"]}</text>')
    for v in range(0, 101, 25):
        out.append(f'<line x1="{x(v):.1f}" y1="{top - 8}" x2="{x(v):.1f}" y2="{h - 30}" stroke="{GRID}"/>')
        out.append(f'<text x="{x(v):.1f}" y="{h - 12}" text-anchor="middle" fill="{MUTED}">{v}%</text>')
    for i, (lab, col) in enumerate(zip(t["rp_bars"], ("#111827", "#93c5fd"), strict=True)):
        out.append(f'<rect x="{left + i * 330}" y="{top - 50}" width="12" height="12" fill="{col}"/>')
        out.append(f'<text x="{left + i * 330 + 18}" y="{top - 40}" font-size="12">{lab}</text>')
    out.append(f'<path d="M{left + 6} {top - 70} l6 6 l-6 6 l-6 -6 z" fill="#dc2626"/>')
    out.append(f'<text x="{left + 18}" y="{top - 60}" font-size="12">{t["rp_lr"]}</text>')
    best_all = rows[-1][7]
    pool_all = 100 * rows[-1][4] / rows[-1][5]
    vals = [(t["rp_task"].format(i=r[0]), 100 * r[7] / r[8], f"{r[7]}/{r[8]}", 100 * r[4] / r[5], f"{r[4]}/{r[5]}") for r in tasks]
    vals.append((t["rp_all"], best_all, "", pool_all, f"{rows[-1][4]}/{rows[-1][5]}"))
    for j, (lab, b, bl, p, pl) in enumerate(vals):
        y = top + j * (2 * bh + gap) + (8 if j == len(tasks) else 0)
        out.append(f'<text x="{left - 10}" y="{y + bh + 4}" text-anchor="end" font-weight="{600 if j == len(tasks) else 400}">{lab}</text>')
        for k, (v, vl, col) in enumerate(((b, bl, "#111827"), (p, pl, "#93c5fd"))):
            yy = y + k * bh
            out.append(f'<rect x="{x(0):.1f}" y="{yy}" width="{max(x(v) - x(0), 1.5):.1f}" height="{bh - 1}" fill="{col}"/>')
            out.append(f'<text x="{x(v) + 5:.1f}" y="{yy + bh - 2}" font-size="11"><tspan font-weight="600">{v:.1f}</tspan>'
                       f'<tspan fill="{MUTED}">{" (" + vl + ")" if vl else ""}</tspan></text>')
        lr = rows[j][11]
        out.append(f'<path d="M{x(lr):.1f} {y + bh - 6} l6 6 l-6 6 l-6 -6 z" fill="#dc2626" stroke="#ffffff" stroke-width="1"/>')
    y = top + len(tasks) * (2 * bh + gap) + 8
    null = rows[-1][10]
    out.append(f'<line x1="{x(null):.1f}" y1="{y - 4}" x2="{x(null):.1f}" y2="{y + bh + 2}" stroke="#f59e0b" stroke-width="3" stroke-dasharray="3 2"/>')
    out.append(f'<text x="{x(null) - 4:.1f}" y="{y + 2 * bh + 14}" text-anchor="middle" font-size="11" fill="#b45309">'
               f'{t["rp_null"].format(p=pool_all, v=null)}</text>')
    return svg(w, h, out)


def matched100_rows():
    """Each run independently: first ten initial states of every task, never the first 100 global rows."""
    rows = []
    for side in ("official", "lerobot"):
        for condition, runs in OP_RUNS[side].items():
            for repeat, run in enumerate(runs, 1):
                per = sorted(json.loads((ROOT / "dashboard/data" / run / "eval_info.json").read_text())["per_task"], key=lambda task: task["task_id"])
                if len(per) != 10 or any(len(task["metrics"]["successes"]) < 10 for task in per):
                    raise ValueError(f"missing matched100 states: {run}")
                success = sum(bool(value) for task in per for value in task["metrics"]["successes"][:10])
                source_episodes = sum(len(task["metrics"]["successes"]) for task in per)
                rows.append([side, condition, repeat, run, source_episodes, "first10_per_task", 100, success, float(success)])
    return rows


def fig_official_pi0(summary, t):
    # Full500 rates stay in the historical CSV; display matched100 points only.
    rows = matched100_rows()
    conditions = OP_BARS + ["wrist_frozen"]
    labels = t["op_conds"] + (["Wrist frozen"] if t is TXT["en"] else ["只冻结腕部"])
    w, left, top, step, h = 900, 190, 106, 56, 580
    x = lambda pc: left + 620 * pc / 100
    out = [title(t["op_title"])]
    colors = {"official": BLUE, "lerobot": ORANGE}
    for i, side in enumerate(colors):
        out.append(f'<circle cx="{left+i*320}" cy="56" r="4" fill="{colors[side]}"/>')
        out.append(f'<text x="{left+12+i*320}" y="60">{t["op_models"][side]}</text>')
    for v in range(0, 101, 25):
        out.append(f'<line x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{top-15}" y2="{top+len(conditions)*step-15}" stroke="{GRID}"/>')
        out.append(f'<text x="{x(v):.1f}" y="{h-50}" text-anchor="middle">{v}%</text>')
    for i, (condition, label) in enumerate(zip(conditions, labels, strict=True)):
        y = top + i * step
        out.append(f'<text x="{left-14}" y="{y+7}" text-anchor="end">{label}</text>')
        for side, offset in (("official", -6), ("lerobot", 11)):
            values = [row[-1] for row in rows if row[0] == side and row[1] == condition]
            cy = y + offset
            for j, value in enumerate(values):
                jitter = (j-(len(values)-1)/2)*4
                out.append(f'<circle cx="{x(value):.1f}" cy="{cy+jitter:.1f}" r="3.2" fill="{colors[side]}"/>')
            label_value = "/".join(str(int(v)) for v in values)
            out.append(f'<text x="{x(max(values))+10:.1f}" y="{cy+4}" font-size="11" fill="{colors[side]}">{label_value}</text>')
    note = (
        "Full500 normal references: official 482/500; LeRobot 360/500. Weights and pipelines both differ."
        if t is TXT["en"] else "完整500正常另列参考：官方482/500；LeRobot360/500。两边权重与管线均不同，不能唯一归因。"
    )
    out.append(f'<text x="20" y="{h-15}" font-size="11" fill="{MUTED}">{note}</text>')
    return svg(w, h, out)


def fig_blackout_overview(summary, t):
    cn = t is TXT["zh"]
    w, h, left, top = 900, 342, 210, 105
    x = lambda pc: left + 580 * pc / 100
    heading = "四模型探索：正常画面与全部视觉输入涂黑" if cn else "Four-policy exploration: normal vision vs. all-black input"
    out = [title(heading)]
    note = (
        "各100回合代表性运行；正常取每任务前10初态。OpenVLA仅有主视角，其余为双视角。"
        if cn else "Representative 100-episode runs; first10 states/task. OpenVLA: agent only; others: two cameras."
    )
    out.append(f'<text x="20" y="50" font-size="12" fill="{MUTED}">{note}</text>')
    for v in range(0, 101, 25):
        out.append(f'<line x1="{x(v):.1f}" x2="{x(v):.1f}" y1="80" y2="290" stroke="{GRID}"/>')
        out.append(f'<text x="{x(v):.1f}" y="310" text-anchor="middle">{v}%</text>')
    names = {"pi0": "LeRobot π0 v044", "pi0.5": "LeRobot π0.5 v044", "SmolVLA": "SmolVLA", "OpenVLA": "OpenVLA"}
    by = {row["model"]: row for row in summary}
    for i, key in enumerate(["pi0.5", "OpenVLA", "SmolVLA", "pi0"]):
        row = by[key]; normal, black = sum(row["normal"]), sum(row["black"]); y = top+i*52
        out.append(f'<text x="20" y="{y+4}">{names[key]}</text>')
        out.append(f'<line x1="{x(black):.1f}" x2="{x(normal):.1f}" y1="{y}" y2="{y}" stroke="#aeb8c5" stroke-width="2"/>')
        for pc, color, dy in [(normal, BLUE, -10), (black, ORANGE, 18)]:
            out.append(f'<circle cx="{x(pc):.1f}" cy="{y}" r="5" fill="{color}"/>')
            out.append(f'<text x="{x(pc):.1f}" y="{y+dy}" text-anchor="middle" fill="{color}">{pc}</text>')
    legend = (
        "蓝：正常　橙：全黑　｜　π0全黑重复范围53–56%；重复不是新增初态。"
        if cn else "Blue: normal; orange: black. π0 black repeats:53–56%; repeats are not new initial states."
    )
    out.append(f'<text x="20" y="334" font-size="12" fill="{MUTED}">{legend}</text>')
    return svg(w, h, out)


def load_dashboard():
    s = (ROOT / "dashboard" / "results.js").read_text()
    return {m.group(1): json.loads(m.group(2)) for m in re.finditer(r"window\.(\w+) = (.*?);\n(?=window\.|\Z)", s, re.S)}


def write_csv(name, header, rows):
    with open(RES / name, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n" if name in {"official_pi0_matched100.csv", "official_pi0_summary.csv"} else "\r\n")
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
    """本项目参考对照判据（非等效检验），缺少参考范围则用单点。"""
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
    """每个任务一行、两幅俯视图：左 = 正常重跑参考，右 = 正常 vs 全涂黑。坐标为机器人基座系 XY(cm)，各行同一比例尺。"""
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


def fig_inputs(t, mobile=False):
    """Camera interventions and held-fixed inputs, with a compact orthogonal flow."""
    en = t["in_policy"] == "Policy"
    w, h = (420, 500) if mobile else (880, 350)
    width = 380 if mobile else 420
    camera_y, fixed_y = 54, 206
    blue, pale, edge, grey = "#285d8a", "#f1f6fa", "#cedde8", "#64717c"
    words = {
        "title": "Camera ablations: inputs and intervention" if en else "相机消融：输入与干预",
        "camera": "Camera images" if en else "相机画面",
        "changed": "Intervened" if en else "实验中改变",
        "operations": "Black out · add noise · freeze · mask slot" if en else "涂黑 · 加噪声 · 冻结 · 槽位屏蔽",
        "fixed": "Other inputs" if en else "其他输入",
        "same": "Held fixed" if en else "保持不变",
        "foot": "Two-camera policies shown. OpenVLA uses only the agent view and instruction."
                if en else "图示双相机策略。OpenVLA 仅接收主视角画面与任务指令。",
    }
    out = [f'<title>{words["title"]}</title>',
           '<defs><marker id="input-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto">'
           f'<path d="M1 1 L7 4 L1 7" fill="none" stroke="{grey}" stroke-width="1.2"/></marker></defs>',
           f'<text x="20" y="29" font-size="17" font-weight="600">{words["title"]}</text>',
           f'<rect x="20" y="{camera_y}" width="{width}" height="128" rx="7" fill="{pale}" stroke="{edge}"/>',
           f'<text x="36" y="80" font-size="14" font-weight="600" fill="{blue}">{words["camera"]}</text>',
           f'<text x="{width + 4}" y="80" text-anchor="end" font-size="12" fill="{blue}">{words["changed"]}</text>']
    for i, key in enumerate(("in_agent", "in_wrist")):
        x = 36 + i * (174 if mobile else 196)
        out.append(f'<g transform="translate({x} 101)" stroke="{blue}" stroke-width="1.4" fill="none">'
                   '<rect x="0" y="3" width="25" height="17" rx="2"/><path d="M6 3 L9 0 H17 L20 3"/>'
                   '<circle cx="12.5" cy="11.5" r="4.5"/></g>')
        out.append(f'<text x="{x + 34}" y="116" font-size="{13 if en else 15}" font-weight="500">{t[key]}</text>')
    out += [f'<line x1="36" y1="137" x2="{width + 4}" y2="137" stroke="{edge}"/>',
            f'<text x="36" y="163" font-size="{12 if en else 13}" fill="{blue}">{words["operations"]}</text>',
            f'<text x="36" y="{fixed_y + 3}" font-size="14" font-weight="600">{words["fixed"]}</text>',
            f'<text x="{width + 4}" y="{fixed_y + 3}" text-anchor="end" font-size="12" fill="{grey}">{words["same"]}</text>',
            f'<line x1="36" y1="{fixed_y + 14}" x2="{width + 4}" y2="{fixed_y + 14}" stroke="#dde2e6"/>']
    for i, (key, sub) in enumerate((("in_state", "in_sub_state"), ("in_lang", "in_sub_lang"))):
        y = fixed_y + 41 + i * (43 if mobile else 36)
        if mobile:
            out += [f'<text x="36" y="{y}" font-size="14" font-weight="500">{t[key]}</text>',
                    f'<text x="36" y="{y + 19}" font-size="12" fill="{grey}">{t[sub]}</text>']
        else:
            out.append(f'<text x="36" y="{y}" font-size="14" font-weight="500">{t[key]}</text>')
            out.append(f'<text x="{154 if en else 144}" y="{y}" font-size="12" fill="{grey}">{t[sub]}</text>')
    if mobile:
        path = 'M400 118 H410 V355 H194 V377'
        out.append(f'<path d="{path}" fill="none" stroke="{grey}" stroke-width="1.2" marker-end="url(#input-arrow)"/>')
        out.append(f'<path d="M400 264 H410" fill="none" stroke="{grey}" stroke-width="1.2"/>')
        px, py = 130, 386
    else:
        out.append(f'<path d="M440 118 H476 V265 H440" fill="none" stroke="{grey}" stroke-width="1.2"/>')
        out.append(f'<path d="M476 194 H526" fill="none" stroke="{grey}" stroke-width="1.2" marker-end="url(#input-arrow)"/>')
        px, py = 538, 167
    out += [f'<rect x="{px}" y="{py}" width="128" height="54" rx="5" fill="#fff" stroke="{blue}"/>',
            f'<text x="{px + 64}" y="{py + 33}" text-anchor="middle" font-size="16" font-weight="600">{t["in_policy"]}</text>',
            f'<path d="M{px + 128} {py + 27} H{px + 182}" fill="none" stroke="{grey}" stroke-width="1.2" marker-end="url(#input-arrow)"/>',
            f'<text x="{px + 196}" y="{py + 32}" font-size="15" font-weight="500">{t["in_action"]}</text>']
    if mobile and en:
        out += [f'<text x="20" y="474" font-size="11" fill="{grey}">Two-camera policies shown. OpenVLA uses only</text>',
                f'<text x="20" y="490" font-size="11" fill="{grey}">the agent view and instruction.</text>']
    else:
        out.append(f'<text x="20" y="{h - 12}" font-size="{10 if mobile else 12}" fill="{grey}">{words["foot"]}</text>')
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
    write_csv("official_pi0_matched100.csv", ["side", "condition", "repeat", "raw_run", "source_episodes", "subset", "episodes", "successes", "success_pc"], matched100_rows())
    rp_sum = replay_summary()
    write_csv("open_loop_replay.csv", ["task", "source_successes", "self_successes", "self_replays", "cross_successes", "cross_replays",
                                       "best_source", "best_successes", "best_replays", "object_max_span_cm",
                                       "best_expected_if_equal_pc", "lerobot_black_pc"], rp_sum)
    traj = [json.loads((RES / f"trajectories_task{i}.json").read_text()) for i in TRAJ_TASKS]
    for lang, out in (("en", MEDIA), ("zh", MEDIA / "zh")):
        t = TXT[lang]
        (out / "blackout_overview.svg").write_text(fig_blackout_overview(d["BLACKOUT"]["summary"], t))
        (out / "reproduction.svg").write_text(fig_reproduction(runs, t))
        (out / "perturbations.svg").write_text(fig_perturbations(pert, t))
        (out / "trajectory.svg").write_text(fig_trajectory(traj, t))
        (out / "inputs.svg").write_text(fig_inputs(t))
        (out / "inputs-mobile.svg").write_text(fig_inputs(t, mobile=True))
        (out / "single_camera.svg").write_text(fig_single_camera(sc_sum, t))
        (out / "official_pi0.svg").write_text(fig_official_pi0(op_sum, t))
        (out / "open_loop_replay.svg").write_text(fig_replay(rp_sum, t))
    print(f"wrote {len(list(RES.glob('*.csv')))} csv -> results/, 9 svg -> media/ and media/zh/")
