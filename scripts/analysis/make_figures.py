"""从 dashboard/ 的评测汇总生成 results/*.csv 和 README 用的 SVG 图(只用标准库)。
英文图写到 media/,中文图写到 media/zh/。

用法(仓库根目录): python3 dashboard/build.py && python3 scripts/analysis/make_figures.py
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES, MEDIA = ROOT / "results", ROOT / "media"
FONT = "-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei','Noto Sans CJK SC',sans-serif"
INK, MUTED, GRID = "#1f2933", "#6b7280", "#e5e7eb"
BLUE, RED, ORANGE, VIOLET = "#2563eb", "#dc2626", "#ea580c", "#7c3aed"
MODEL = {"pi0": "π0", "pi0.5": "π0.5"}

TXT = {
    "en": {
        "rep_title": "Public checkpoints: success rate on this machine vs. reference",
        "rep_ours": "This machine (500 episodes, 95% CI)", "rep_ref": "Reference", "rep_fail": "Not reproduced (intervals do not overlap)",
        "pert_title": "Success rate when the camera input is perturbed (LIBERO-Spatial, 100 episodes each)",
        "conds": ["Normal", "Gaussian noise", "Frozen first frame", "Agent-view black", "Wrist black", "All black"],
        "pending": "running",
        "traj_title": "π0 end-effector paths, top view: one task, 10 episodes, identical initial states",
        "traj_a": "Normal vs. normal re-run (noise floor)", "traj_b": "Normal vs. all cameras black",
        "traj_normal": "normal", "traj_rerun": "normal, re-run", "traj_black": "all cameras black", "traj_grasp": "dots = grasp points",
        "traj_start": "start", "traj_scale": "10 cm",
        "in_title": "What the policy receives, and what each experiment changes",
        "in_agent": "Agent-view camera", "in_wrist": "Wrist camera", "in_state": "Robot state", "in_lang": "Instruction",
        "in_policy": "Policy", "in_action": "Action",
        "in_img_note": "evaluation: black / noise / frozen", "in_state_note": "training: zeroed for 50% of samples",
        "in_lang_note": "unchanged", "in_sub_state": "joint and gripper positions", "in_sub_lang": "“pick up the black bowl …”",
    },
    "zh": {
        "rep_title": "公开权重复现:本机成功率 vs 基准",
        "rep_ours": "本机(500 回合,95% 置信区间)", "rep_ref": "基准", "rep_fail": "未复现(区间不重叠)",
        "pert_title": "扰动相机输入后的成功率(LIBERO-Spatial,每组 100 回合)",
        "conds": ["正常", "加高斯噪声", "冻结首帧", "只涂主视角", "只涂腕部", "全涂黑"],
        "pending": "在跑",
        "traj_title": "π0 末端执行器路线(俯视):同一任务,10 个回合,初始状态相同",
        "traj_a": "正常 vs 正常重跑(噪声底线)", "traj_b": "正常 vs 相机全涂黑",
        "traj_normal": "正常", "traj_rerun": "正常(重跑)", "traj_black": "相机全涂黑", "traj_grasp": "圆点 = 抓取点",
        "traj_start": "起点", "traj_scale": "10 cm",
        "in_title": "策略收到什么输入,各实验改了哪一项",
        "in_agent": "主视角相机", "in_wrist": "腕部相机", "in_state": "机械臂状态", "in_lang": "任务指令",
        "in_policy": "策略", "in_action": "动作",
        "in_img_note": "评测时:涂黑 / 加噪声 / 冻结", "in_state_note": "训练时:50% 样本置零",
        "in_lang_note": "不改", "in_sub_state": "关节与夹爪位置", "in_sub_lang": "“把黑碗拿起来放到……”",
    },
}
COND_KEYS = ["normal", "noise", "freeze", "agent_black", "wrist_black", "all_black"]
COND_COL = ["#9ca3af", "#86efac", "#14b8a6", "#60a5fa", "#f59e0b", "#111827"]


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
    """粗略估计文字宽度(像素),用于排图例。"""
    return sum(size * (0.56 if c.isascii() else 1.0) for c in s)


def reproduced(r):
    """本机区间与基准区间(没有则取基准点)是否重叠。"""
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
           f'<text x="{lx2 + 14:.0f}" y="50" fill="{MUTED}">{t["rep_ref"]}</text>',
           f'<circle cx="{lx3:.0f}" cy="46" r="5" fill="{RED}"/><text x="{lx3 + 12:.0f}" y="50" fill="{MUTED}">{t["rep_fail"]}</text>']
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
        if abs(r["pc"] - r["baseline_pc"]) > 6:  # 离得远才单独标基准值,避免重叠
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
            v, bx = m[key], x0 + i * (bw + gap)
            if v is None:
                out.append(f'<text x="{bx + bw / 2:.1f}" y="{y(0) - 6:.1f}" text-anchor="middle" font-size="10" fill="{MUTED}">{t["pending"]}</text>')
                continue
            out.append(f'<rect x="{bx:.1f}" y="{y(max(v, 0.8)):.1f}" width="{bw}" height="{ph - (y(max(v, 0.8)) - top):.1f}" rx="2" fill="{col}"/>')
            out.append(f'<text x="{bx + bw / 2:.1f}" y="{y(v) - 5:.1f}" text-anchor="middle" font-size="12" font-weight="600">{v}</text>')
        out.append(f'<text x="{left + gw * (g + 0.5):.1f}" y="{h - 16}" text-anchor="middle" font-weight="600">{MODEL.get(m["model"], m["model"])}</text>')
    return svg(w, h, out)


def fig_trajectory(traj, t):
    """两幅俯视图:左 = 正常两次(噪声底线),右 = 正常 vs 全涂黑。坐标为机器人基座系 XY(cm)。"""
    runs = traj["runs"]
    pts = [p for eps in runs.values() for e in eps for p in e["xy"]]
    x0, x1 = min(p[0] for p in pts) - 2, max(p[0] for p in pts) + 2
    y0, y1 = min(p[1] for p in pts) - 2, max(p[1] for p in pts) + 2
    pw, top, pad = 340, 92, 26
    s = (pw - 20) / (y1 - y0)  # 画面横向 = 机器人 Y,纵向 = 机器人 X
    phh = s * (x1 - x0) + 20
    w, h = pad * 2 + pw * 2 + 28, top + phh + 26
    out = [title(t["traj_title"])]

    def panel(ox, name, a, b, ca, cb, la, lb):
        X = lambda p: ox + 10 + s * (p[1] - y0)
        Y = lambda p: top + 10 + s * (p[0] - x0)
        lx = ox + 23 + tw(la) + 16
        o = [f'<rect x="{ox}" y="{top}" width="{pw}" height="{phh:.1f}" rx="6" fill="#f9fafb" stroke="{GRID}"/>',
             f'<text x="{ox}" y="{top - 34}" font-weight="600">{name}</text>',
             f'<line x1="{ox}" y1="{top - 16}" x2="{ox + 18}" y2="{top - 16}" stroke="{ca}" stroke-width="2.5"/>'
             f'<text x="{ox + 23}" y="{top - 12}" fill="{MUTED}">{la}</text>',
             f'<line x1="{lx:.0f}" y1="{top - 16}" x2="{lx + 18:.0f}" y2="{top - 16}" stroke="{cb}" stroke-width="2.5"/>'
             f'<text x="{lx + 23:.0f}" y="{top - 12}" fill="{MUTED}">{lb}</text>']
        for run, col in ((a, ca), (b, cb)):
            for e in runs[run]:
                d = " ".join(f"{X(p):.1f},{Y(p):.1f}" for p in e["xy"])
                o.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="1.3" opacity="0.55" stroke-linejoin="round"/>')
        for run, col in ((a, ca), (b, cb)):
            for e in runs[run]:
                if e["grasp"]:
                    o.append(f'<circle cx="{X(e["grasp"]):.1f}" cy="{Y(e["grasp"]):.1f}" r="3.6" fill="{col}" stroke="#ffffff" stroke-width="1"/>')
        st = runs[a][0]["xy"][0]
        o.append(f'<circle cx="{X(st):.1f}" cy="{Y(st):.1f}" r="4.5" fill="none" stroke="{INK}" stroke-width="1.5"/>'
                 f'<text x="{X(st):.1f}" y="{Y(st) - 9:.1f}" text-anchor="middle" font-size="11" fill="{INK}">{t["traj_start"]}</text>')
        bx, by = ox + pw - 14 - 10 * s, top + phh - 12
        o.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{bx + 10 * s:.1f}" y2="{by:.1f}" stroke="{INK}" stroke-width="2"/>'
                 f'<text x="{bx + 5 * s:.1f}" y="{by - 5:.1f}" text-anchor="middle" font-size="11" fill="{MUTED}">{t["traj_scale"]}</text>')
        return o

    out += panel(pad, t["traj_a"], "traj_pi0_normal", "traj_pi0_normal2", BLUE, VIOLET, t["traj_normal"], t["traj_rerun"])
    out += panel(pad + pw + 28, t["traj_b"], "traj_pi0_normal", "traj_pi0_black", BLUE, ORANGE, t["traj_normal"], t["traj_black"])
    out.append(f'<text x="{w - pad:.0f}" y="{h - 8:.0f}" text-anchor="end" font-size="11" fill="{MUTED}">{t["traj_grasp"]}</text>')
    return svg(w, h, out)


def fig_inputs(t):
    w, h, bx, bw, bh = 760, 300, 30, 330, 46
    rows = [("in_agent", None, "in_img_note", ORANGE), ("in_wrist", None, "in_img_note", ORANGE),
            ("in_state", "in_sub_state", "in_state_note", VIOLET), ("in_lang", "in_sub_lang", "in_lang_note", MUTED)]
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
              [[r["model"], r["task"], r["checkpoint"], r["n"], r["pc"], r["ci"], r["baseline_pc"], r["baseline_src"], int(reproduced(r))] for r in runs])
    write_csv("blackout_per_task.csv", ["model", "condition"] + [f"task{i}" for i in range(10)] + ["total"],
              [[m["model"], c] + m[c] + [sum(m[c])] for m in d["BLACKOUT"]["summary"] for c in ("normal", "black")])
    cam = {m["model"]: m for m in fu["cam"]}
    pert = [{**p, "agent_black": cam[p["model"]]["agent_black"], "wrist_black": cam[p["model"]]["wrist_black"]} for p in fu["perturb"]]
    write_csv("perturbations.csv", ["model"] + COND_KEYS, [[m["model"]] + ["" if m[k] is None else m[k] for k in COND_KEYS] for m in pert])
    write_csv("trajectory.csv", ["pair", "dtw_mean_cm", "grasp_dist_mean_cm", "n_grasp_pairs"],
              [[k, round(v["dtw_mean"], 2), round(v["grasp_dist_mean"], 2), v["n_grasp_pairs"]] for k, v in fu["traj"]["pairs"].items()])
    write_csv("finetune_statedrop.csv", ["model", "normal", "all_black", "note"], [[f["name"], f["normal"], f["black"], f["note"]] for f in fu["finetune"]])
    traj = json.loads((RES / "trajectories_task1.json").read_text())
    for lang, out in (("en", MEDIA), ("zh", MEDIA / "zh")):
        t = TXT[lang]
        (out / "reproduction.svg").write_text(fig_reproduction(runs, t))
        (out / "perturbations.svg").write_text(fig_perturbations(pert, t))
        (out / "trajectory.svg").write_text(fig_trajectory(traj, t))
        (out / "inputs.svg").write_text(fig_inputs(t))
    print(f"wrote {len(list(RES.glob('*.csv')))} csv -> results/, 4 svg -> media/ and media/zh/")
