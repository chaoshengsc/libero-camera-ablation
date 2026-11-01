"""Recompute P1/P2 tables, paired bootstrap intervals and bilingual figures.

Run from the repository root: python scripts/analysis/summarize_followup.py
Requires NumPy, never imports a policy or simulator. Full NPZ audits are separate
from the outcome/pairing records exported into dashboard/data/.
"""

import csv
import hashlib
import json
import math
from collections import Counter
from html import escape
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "dashboard/data"
GROUPS = {"A": ("normal", "live"), "B": ("black", "live"),
          "C": ("normal", "freeze_initial"), "D": ("black", "freeze_initial")}
SELECTED = [1, 7, 1, 1, 0, 1, 3, 2, 3, 0]
SEED, DRAWS = 20261031, 20000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def array_hash(a):
    a = np.ascontiguousarray(a)
    header = json.dumps({"dtype": a.dtype.str, "shape": list(a.shape)}, sort_keys=True)
    return hashlib.sha256(header.encode() + b"\n" + a.tobytes()).hexdigest()


def checked_data(directory):
    directory = Path(directory)
    meta = json.loads((directory / "metadata.json").read_text())
    for name, expected in meta["files"].items():
        path = directory / name
        assert directory.resolve() in path.resolve().parents, name
        assert sha(path) == expected, f"source hash mismatch: {name}"
    assert meta["bootstrap_seed"] == SEED and meta["bootstrap_draws"] == DRAWS
    return meta


def wilson(k, n):
    z = 1.959963984540054
    p, den = k / n, 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [0.0 if k == 0 else 100 * max(0, center - half),
            100.0 if k == n else 100 * min(1, center + half)]


def load_state_feedback(directory=None):
    directory = Path(directory or DATA / "state_feedback")
    meta = checked_data(directory)
    assert meta["checkpoint"] == "lerobot/pi0_libero_finetuned_v044@45dcc8fc"
    assert (meta["rendering"], meta["n_action_steps"]) == (360, 5)
    expected = [(stage, group) for stage in ("smoke", "r0", "r1", "r2") for group in GROUPS]
    assert [(r["stage"], r["group"]) for r in meta["runs"]] == expected
    y = np.zeros((10, 10, 3, 4), dtype=int)
    episodes, runs, tasks, paired = [], [], [], {}
    for run in meta["runs"]:
        stage, group, repeat = run["stage"], run["group"], run["repeat"]
        n = 1 if stage == "smoke" else 10
        assert repeat == (0 if stage == "smoke" else int(stage[1:])) and run["exit_code"] == 0
        path = directory / run["id"]
        info = json.loads((path / "eval_info.json").read_text())
        pairing = json.loads((path / "pairing.json").read_text())
        image, state = GROUPS[group]
        assert (pairing["blackout"], pairing["mode"]) == ("none" if image == "normal" else "all", state)
        per = sorted(info["per_task"], key=lambda t: t["task_id"])
        assert [t["task_id"] for t in per] == list(range(10))
        assert all(len(t["metrics"]["successes"]) == n for t in per)
        succ = [int(s) for t in per for s in t["metrics"]["successes"]]
        assert len(pairing["episodes"]) == len(succ) == info["overall"]["n_episodes"] == 10 * n
        assert math.isclose(info["overall"]["pc_success"], 100 * sum(succ) / len(succ), abs_tol=1e-8)
        assert [(r["task"], r["initial"]) for r in pairing["episodes"]] == [(t, i) for t in range(10) for i in range(n)]
        for index, row in enumerate(pairing["episodes"]):
            task, initial = row["task"], row["initial"]
            assert row["repeat"] == repeat and row["seeded"] and row["masks"] == [True, True, False]
            assert row["noise_seed"] == SEED + 1000 * repeat + 50 * task + initial
            key = stage, task, initial
            value = row["first_frame_hash"], row["eef0"], row["noise_seed"]
            if key in paired:
                assert value == paired[key], f"unpaired P1 initial state: {key}"
            else:
                paired[key] = value
            episodes.append({"stage": stage, "group": group, "repeat": repeat, "task": task, "initial": initial,
                             "success": succ[index], "noise_seed": row["noise_seed"],
                             "first_frame_hash": row["first_frame_hash"], "state_changed": int(row["state_changes"]),
                             "sent_changed": int(row["sent_changes"]), "inference_blocks": row["image_checks"]})
            if stage != "smoke":
                y[task, initial, repeat, list(GROUPS).index(group)] = succ[index]
        k = sum(succ)
        lower, upper = wilson(k, len(succ))
        runs.append({"stage": stage, "group": group, "repeat": repeat, "episodes": len(succ), "successes": k,
                     "success_pc": 100 * k / len(succ), "wilson_lo": lower, "wilson_hi": upper})
        tasks += [{"stage": stage, "group": group, "repeat": repeat, "task": t["task_id"], "episodes": n,
                   "successes": sum(t["metrics"]["successes"])} for t in per]
    assert len(episodes) == 1240 and len(runs) == 16
    return y, episodes, runs, tasks


def state_bootstrap(y):
    assert y.shape == (10, 10, 3, 4) and np.isin(y, [0, 1]).all()
    # Match the original NumPy PCG64 sampling order, preserving all repeats and groups.
    state_means = y.mean(axis=2)
    indices = np.random.default_rng(SEED).integers(0, 10, size=(DRAWS, 10, 10))
    boot = state_means[np.arange(10)[None, :, None], indices].mean(axis=(1, 2)) * 100
    point = state_means.mean(axis=(0, 1)) * 100
    contrasts = {"black_live_minus_frozen": ([0, 1, 0, -1], "primary"),
                 "vision_live_minus_frozen": ([1, 0, -1, 0], "secondary"),
                 "interaction_black_minus_vision": ([-1, 1, 1, -1], "exploratory")}
    rows = []
    for name, (weights, role) in contrasts.items():
        values = (boot * weights).sum(axis=1)
        lower, upper = np.quantile(values, [0.025, 0.975])
        rows.append({"comparison": name, "role": role, "difference_pp": float((point * weights).sum()),
                     "ci95_lo": float(lower), "ci95_hi": float(upper)})
    return point.tolist(), rows


def load_replay_holdout(directory=None):
    directory = Path(directory or DATA / "replay_holdout")
    checked_data(directory)
    selection = json.loads((directory / "selection.json").read_text())
    outcomes = json.loads((directory / "outcomes.json").read_text())
    source = json.loads((directory / "source_actions.json").read_text())
    assert source["dtype"] == "<f4" and set(source["actions"]) == {str(i) for i in range(10)}
    assert [r["task"] for r in selection["tasks"]] == list(range(10))
    assert [r["source_initial"] for r in selection["tasks"]] == SELECTED
    prior = json.loads((DATA / "official_pi0/ojx360_replay/replay.json").read_text())
    actions = []
    for task, row in enumerate(selection["tasks"]):
        old = prior["tasks"][task]
        candidates = [i for i, ok in enumerate(old["source_success"]) if ok]
        chosen = min(candidates, key=lambda i: (-sum(old["cross"][str(i)].values()), i))
        assert chosen == SELECTED[task] and row["targets"] == list(range(10, 50))
        a = np.asarray(source["actions"][str(task)], dtype=np.dtype(source["dtype"]))
        assert a.shape == tuple(row["shape"]) and np.isfinite(a).all()
        assert a.shape[1] == 7 and 0 < len(a) <= 280
        assert array_hash(a) == row["action_hash"]
        assert array_hash(a.astype(np.float64)) == row["float64_action_hash"]
        actions.append(a)
    assert not outcomes["invalid"]
    assert len(outcomes["self"]) == 10 and len(outcomes["formal"]) == 400
    assert [(r["task"], r["target"]) for r in outcomes["self"]] == list(enumerate(SELECTED))
    assert [(r["task"], r["target"]) for r in outcomes["formal"]] == [(t, i) for t in range(10) for i in range(10, 50)]
    for stage in ("self", "formal"):
        for row in outcomes[stage]:
            task = row["task"]
            assert row["valid"] and row["source_initial"] == SELECTED[task]
            assert row["source_action_hash"] == selection["tasks"][task]["action_hash"]
            assert row["source_length"] == len(actions[task]) and 0 < row["steps"] <= row["source_length"]
            assert row["seed"] == 1000 + row["target"]
            assert row["sent_action_hash"] == array_hash(actions[task][:row["steps"]].astype(np.float64))
            assert row["success"] == (row["reason"] == "success")
    assert sum(r["success"] for r in outcomes["self"]) >= 8
    return selection, outcomes, actions


def replay_statistics(outcomes, selection):
    y = np.array([r["success"] for r in outcomes["formal"]], dtype=bool).reshape(10, 40)
    indices = np.random.default_rng(SEED).integers(0, 40, size=(DRAWS, 10, 40))
    boot = y[np.arange(10)[None, :, None], indices].mean(axis=(1, 2)) * 100
    interval = np.quantile(boot, [0.025, 0.975]).tolist()
    rows = []
    for task in range(10):
        k = int(y[task].sum())
        lo, hi = wilson(k, 40)
        rows.append({"task": task, "source_initial": SELECTED[task], "source_length": selection["tasks"][task]["shape"][0],
                     "episodes": 40, "successes": k, "success_pc": 100 * k / 40,
                     "ci95_lo": lo, "ci95_hi": hi, "interval_method": "Wilson"})
    rows.append({"task": "all", "source_initial": "", "source_length": "", "episodes": 400,
                 "successes": int(y.sum()), "success_pc": float(y.mean() * 100),
                 "ci95_lo": interval[0], "ci95_hi": interval[1], "interval_method": "within-task target bootstrap"})
    return rows


def write_csv(name, rows):
    with (ROOT / "results" / name).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: round(v, 6) if isinstance(v, float) else v for k, v in row.items()})


def text(x, y, value, size=13, anchor="start", color="#26313b"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
            f'fill="{color}">{escape(str(value))}</text>')


def save_svg(path, height, body):
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" '
                    f'viewBox="0 0 1000 {height}" font-family="Arial,PingFang SC,Microsoft YaHei,sans-serif">'
                    f'<rect width="1000" height="{height}" fill="white"/>' + "".join(body) + '</svg>\n')


def figures(point, comparisons, runs, replay):
    for lang, path in [("en", ROOT / "media"), ("zh", ROOT / "media/zh")]:
        zh = lang == "zh"
        title = "状态更新敏感性：LeRobot π0 v044" if zh else "State-input update sensitivity | LeRobot pi0 v044"
        body = [text(30, 36, title, 23),
                text(30, 64, "100 个初始状态，各重复三次；每轮四条件配对" if zh else
                     "100 initial states, three repeats; four conditions paired within each repeat")]
        labels = ["正常画面 / 实时状态", "全黑画面 / 实时状态", "正常画面 / 冻结首状态", "全黑画面 / 冻结首状态"] if zh else [
            "Normal images / live state", "Black images / live state", "Normal images / frozen state", "Black images / frozen state"]
        for pc in range(0, 101, 20):
            x = 350 + pc * 4.5
            body += [f'<path d="M{x} 85V275" stroke="#e0e5e9"/>', text(x, 296, f"{pc}%", 12, "middle")]
        for i, (group, label) in enumerate(zip(GROUPS, labels, strict=True)):
            yy, color = 110 + 48 * i, "#2563ab" if group in "AC" else "#bc5428"
            body.append(text(30, yy + 5, f"{group}  {label}", 15))
            for j, run in enumerate(r for r in runs if r["group"] == group and r["stage"] != "smoke"):
                body.append(f'<circle cx="{350 + run["success_pc"] * 4.5}" cy="{yy + (j-1)*5}" r="3.5" fill="{color}"/>')
            body.append(text(950, yy + 5, f"{point[i]:.1f}%", 16, "end"))
        primary = comparisons[0]
        body += [text(30, 340, "全黑：实时状态 − 冻结首状态" if zh else "Black images: live minus frozen state", 17),
                 text(30, 371, f'{primary["difference_pp"]:.1f} pp  [95% CI {primary["ci95_lo"]:.1f}, {primary["ci95_hi"]:.1f}]', 18),
                 text(30, 410, "圆点为三次运行；右侧为均值。重复不是新增独立状态。" if zh else
                      "Dots are three runs; right-hand labels are means. Repeats are not independent states.", 12),
                 text(30, 435, "区间按初始状态成组重采样，固定十任务；尚不能区分纠偏、阶段线索或输入失配。" if zh else
                      "Intervals group repeats by initial state within ten fixed tasks; the mechanism remains unresolved.", 12)]
        save_svg(path / "state_feedback.svg", 460, body)
        body = [text(30, 36, "固定动作在选择外状态上的表现" if zh else "Fixed actions on selection-external states", 23),
                text(30, 64, "官方 OpenPI π0 来源动作；十任务，各四十个目标状态；不调用模型" if zh else
                     "OpenPI pi0 source actions | ten tasks x 40 target states | no model inference")]
        for pc in range(0, 101, 20):
            x = 345 + pc * 4.2
            body += [f'<path d="M{x} 90V510" stroke="#e0e5e9"/>', text(x, 536, f"{pc}%", 12, "middle")]
        for i, row in enumerate(replay[:-1]):
            yy = 110 + i * 40
            x, lo, hi = [345 + pc * 4.2 for pc in (row["success_pc"], row["ci95_lo"], row["ci95_hi"])]
            label = f'任务 {i} / 来源状态 {row["source_initial"]}' if zh else f'Task {i} / source state {row["source_initial"]}'
            body += [text(30, yy + 5, label, 15),
                     f'<path d="M{lo} {yy}H{hi}" stroke="#2563ab" stroke-width="3"/>',
                     f'<circle cx="{x}" cy="{yy}" r="4.5" fill="#2563ab"/>',
                     text(950, yy + 5, f'{row["successes"]}/40 ({row["success_pc"]:.1f}%)', 14, "end")]
        total = replay[-1]
        body += [text(30, 578, f'{total["successes"]}/400 = {total["success_pc"]:.1f}%  |  95% CI '
                      f'[{total["ci95_lo"]:.1f}, {total["ci95_hi"]:.1f}]%', 20),
                 text(30, 612, "逐任务误差线为 Wilson 区间；总体为任务内目标状态分层 bootstrap 区间。" if zh else
                      "Task bars: Wilson intervals. Overall: bootstrap of target states within fixed tasks.", 12),
                 text(30, 637, "目标状态未参与动作选择，但不是隐藏测试集；底层控制器仍有反馈。" if zh else
                      "Targets were excluded from action selection, not previously unseen; the low-level controller retains feedback.", 12),
                 text(30, 662, "固定动作基线不识别 LeRobot π0 的内部机制，不能与其全黑成功率相减归因。" if zh else
                      "This baseline does not identify the LeRobot pi0 mechanism or a fraction of its all-black success.", 12)]
        save_svg(path / "replay_holdout.svg", 690, body)


def main():
    (ROOT / "results").mkdir(exist_ok=True)
    y, episodes, runs, tasks = load_state_feedback()
    point, comparisons = state_bootstrap(y)
    selection, outcomes, _ = load_replay_holdout()
    replay = replay_statistics(outcomes, selection)
    write_csv("state_feedback_episodes.csv", episodes)
    write_csv("state_feedback_runs.csv", runs)
    write_csv("state_feedback_per_task.csv", tasks)
    write_csv("state_feedback_comparisons.csv", comparisons)
    write_csv("replay_holdout_summary.csv", replay)
    replay_rows = [{"stage": stage, **r} for stage in ("self", "formal") for r in outcomes[stage]]
    write_csv("replay_holdout_episodes.csv", replay_rows)
    figures(point, comparisons, runs, replay)
    print(f"P1: {len(episodes)} records (40 smoke + 1200 formal); paired rates {point}")
    print(f"P2: {replay[-1]['successes']}/400; self {sum(r['success'] for r in outcomes['self'])}/10; "
          f"formal reasons {dict(Counter(r['reason'] for r in outcomes['formal']))}")
    print("Wrote 6 CSVs and 4 bilingual SVGs; no model or simulation was run.")


if __name__ == "__main__":
    main()
