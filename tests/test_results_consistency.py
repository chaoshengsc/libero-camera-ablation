"""仓库里的派生结果必须能从原始评测 JSON 重算出来,README 里的数字必须与派生结果一致。"""
import csv
import json
from pathlib import Path

import pytest

from metrics import ci95

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dashboard" / "data"
READMES = [(ROOT / "README.md").read_text(), (ROOT / "README_CN.md").read_text()]


def rows(name):
    return list(csv.DictReader(open(ROOT / "results" / name)))


def per_task(run, first=None):
    """原始 eval_info.json 里各任务的成功次数(first:只数每任务前几回合)。"""
    info = json.loads((DATA / run / "eval_info.json").read_text())
    return [sum(t["metrics"]["successes"][:first]) for t in info["per_task"]]


def test_reproduction_csv_matches_raw_eval_info():
    runs = {"ACT": "act_cube_500", "OpenVLA": "openvla_spatial_500", "SmolVLA": "smolvla2_spatial_500",
            "π0.5": "pi05_spatial_500", "Diffusion Policy": "dp_pusht_500"}
    rs = rows("reproduction.csv")
    assert {r["model"] for r in rs} == set(runs)
    for r in rs:
        info = json.loads((DATA / runs[r["model"]] / "eval_info.json").read_text())
        succ = [s for t in info["per_task"] for s in t["metrics"]["successes"]]
        pc = 100 * sum(succ) / len(succ)
        assert len(succ) == int(r["episodes"]) == 500
        assert round(pc, 1) == float(r["success_pc"])
        assert round(ci95(pc, len(succ)), 1) == float(r["ci95"])
        assert all(f"{float(r['success_pc']):.1f}%" in md for md in READMES)


def test_act_baseline_matches_file_shipped_with_checkpoint():
    """ACT 的基准 83.0% 取自权重仓库自带的 eval_info.json(收录为 baseline_eval_info.json)。"""
    shipped = json.loads((DATA / "act_cube_500" / "baseline_eval_info.json").read_text())
    act = next(r for r in rows("reproduction.csv") if r["model"] == "ACT")
    assert shipped["aggregated"]["pc_success"] == float(act["baseline_pc"]) == 83.0
    assert len(shipped["per_episode"]) == 500


def test_blackout_csv_matches_raw_eval_info():
    raw = {("OpenVLA", "normal"): per_task("openvla_spatial_500", 10), ("SmolVLA", "normal"): per_task("smolvla2_spatial_500", 10),
           ("SmolVLA", "black"): per_task("smol2_black_all"), ("OpenVLA", "black"): per_task("openvla_black_all"), ("π0", "normal"): per_task("pi0_spatial_500", 10),
           ("π0", "black"): per_task("pi0_black_all"), ("π0.5", "normal"): per_task("pi05_spatial_500", 10),
           ("π0.5", "black"): per_task("pi05_black_all")}
    rs = rows("blackout_per_task.csv")
    assert len(rs) == 8  # 4 个模型 × 正常 / 全涂黑
    seen = set()
    for r in rs:
        got = [int(r[f"task{i}"]) for i in range(10)]
        assert sum(got) == int(r["total"])
        key = (r["model"], r["condition"])
        if key in raw:
            assert got == raw[key], key
            seen.add(key)
    assert seen == set(raw)


def test_perturbations_csv_matches_raw_and_readme():
    """1.2 节:每个条件两次运行,CSV、原始数据、README 表格三方一致。"""
    key = {"π0": ("pi0_spatial_500", "pi0", "pi0_black_all"), "π0.5": ("pi05_spatial_500", "pi05", "pi05_black_all"),
           "SmolVLA": ("smolvla2_spatial_500", "smol2", "smol2_black_all")}
    conds = ("normal", "noise", "freeze", "agent_black", "wrist_black", "all_black")
    rs = rows("perturbations.csv")
    assert {r["model"] for r in rs} == set(key) and len(rs) == 6
    by = {(r["model"], r["run"]): r for r in rs}
    for model, (base, k, black) in key.items():
        r1, r2 = by[model, "1"], by[model, "2"]
        assert int(r1["normal"]) == sum(per_task(base, 10))
        for r, d in ((r1, ""), (r2, "run2/")):
            assert int(r["noise"]) == sum(per_task(f"{d}pert_{k}_noise"))
            assert int(r["freeze"]) == sum(per_task(f"{d}pert_{k}_freeze"))
            assert int(r["all_black"]) == sum(per_task(f"{d}{black}"))
            for cam in ("agent", "wrist"):
                assert int(r[f"{cam}_black"]) == sum(per_task(f"{d}traj_{k}_{cam}"))
        if k == "smol2":
            assert r2["normal"] == ""  # SmolVLA 没有第二次正常运行
        else:
            assert int(r2["normal"]) == sum(per_task(f"run2/traj_{k}_normal"))
        line = f"| {model} | " + " | ".join(f"{r1[c]} / {r2[c] or '–'}" for c in conds) + " |"
        assert all(line in md for md in READMES), line


def test_blind_models_stay_at_zero_in_second_run():
    for run in ("pi05_black_all", "openvla_black_all", "smol2_black_all"):
        assert sum(per_task(run)) == sum(per_task(f"run2/{run}")) == 0 and len(per_task(f"run2/{run}")) == 10


def test_pi0_repeated_runs_in_readme():
    """README 里 π0 的重复运行数字:正常 5 次、全涂黑 5 次,以及同一条件两次运行的最大差。"""
    normal = [sum(per_task("pi0_spatial_500", 10))] + [sum(per_task(r)) for r in ("traj_pi0_normal", "traj_pi0_normal2", "run2/traj_pi0_normal", "run2/traj_pi0_normal2")]
    black = [sum(per_task(r)) for r in ("pi0_black_all", "traj_pi0_black", "run2/pi0_black_all", "run2/traj_pi0_black", "run3/pi0_black_all")]
    assert normal == [76, 73, 76, 72, 71] and black == [56, 54, 56, 54, 53]
    by = {(r["model"], r["run"]): r for r in rows("perturbations.csv")}
    gap = lambda m: [abs(int(by[m, "1"][c]) - int(by[m, "2"][c])) for c in ("noise", "freeze", "agent_black", "wrist_black")]
    assert sorted(gap("π0")) == [9, 10, 12, 18] and max(gap("π0.5") + gap("SmolVLA")) == 6
    single = [int(by["π0", n][c]) for n in "12" for c in ("noise", "freeze", "agent_black", "wrist_black")]
    assert (min(single), max(single)) == (59, 80)
    for md in READMES:
        assert "53–56%" in md and "71–76%" in md


def test_section2_checkpoint_rates_in_readme():
    """README 第 2 节注明的 π0 权重 500 回合成功率 73.4%。"""
    for run, pc in (("pi0_spatial_500", "73.4%"),):
        s = per_task(run)
        assert f"{sum(s) / 5:.1f}%" == pc and all(pc in md for md in READMES)


def test_trajectory_summary_numbers_in_readme():
    """README 1.3 的分层数字,两次运行都核对:全涂黑仍成功的任务、噪声底线、任务 7、9、5。"""
    t = {(r["run"], r["metric"], r["pair"]): [float(r[f"task{i}"]) for i in range(10)] for r in rows("trajectory.csv")}
    cell = {"dtw_ok": [], "grasp_ok": [], "dtw_05": [], "grasp_05": [], "dtw_noise": [], "grasp_noise": [], "dtw_7": [], "grasp_7": []}
    for run, ok_expected, same_expected in (("1", [0, 1, 2, 3, 4, 6, 8], [0, 1, 2, 3]), ("2", [0, 1, 2, 3, 4, 6], [0])):
        succ = t[run, "successes", "pi0_all_black"]
        ok = [i for i in range(10) if succ[i] >= 5]
        noise = t[run, "path_dtw_cm", "pi0_normal_vs_rerun"]
        diverged = [i for i in range(10) if noise[i] > 1]
        assert ok == ok_expected and sum(succ) == 54 and succ[7] == 0
        assert [i for i in range(10) if i not in diverged] == same_expected and max(noise[i] for i in same_expected) <= 0.3
        mean = lambda metric, pair, idx: sum(t[run, metric, pair][i] for i in idx) / len(idx)  # noqa: B023
        for key, metric in (("dtw", "path_dtw_cm"), ("grasp", "grasp_distance_cm")):
            cell[f"{key}_ok"].append(mean(metric, "pi0_all_black_vs_normal", ok))
            cell[f"{key}_05"].append(mean(metric, "pi05_vs_pi0_normal", ok))
            cell[f"{key}_noise"].append(mean(metric, "pi0_normal_vs_rerun", diverged))
            cell[f"{key}_7"].append(t[run, metric, "pi0_all_black_vs_normal"][7])
    expected = {"dtw_ok": "2.8 / 3.2", "grasp_ok": "2.4 / 2.2", "dtw_05": "2.9 / 3.0", "grasp_05": "2.6 / 2.5",
                "dtw_noise": "3.4 / 3.3", "grasp_noise": "2.4 / 2.4", "dtw_7": "10.9 / 10.3", "grasp_7": "24.1 / 23.7"}
    for key, (a, b) in cell.items():
        assert f"{a:.1f} / {b:.1f}" == expected[key] and all(f"{expected[key]} cm" in md for md in READMES)
    # 任务 7、9、5 的说明:全涂黑对正常,以及同一任务上两次正常运行之间
    two = lambda pair, i: tuple(f"{t[run, 'path_dtw_cm', pair][i]:.1f}" for run in ("1", "2"))
    assert two("pi0_normal_vs_rerun", 7) == ("2.6", "2.2")
    assert two("pi0_all_black_vs_normal", 9) == ("7.8", "4.9") and two("pi0_normal_vs_rerun", 9) == ("3.3", "3.6")
    assert two("pi0_all_black_vs_normal", 5) == ("6.0", "6.6") and two("pi0_normal_vs_rerun", 5) == ("6.6", "4.7")
    assert [t[run, "successes", "pi0_all_black"][9] for run in ("1", "2")] == [0, 1]
    assert [t[run, "successes", "pi0_all_black"][5] for run in ("1", "2")] == [3, 4]
    spread = json.loads((DATA / "traj_analyze.json").read_text())["grasp_spread"]["traj_pi0_normal"]
    assert sum(spread) / 10 == pytest.approx(1.8, abs=0.05)


def test_no_placeholder_left():
    for md in READMES:
        assert "running" not in md and "在跑" not in md
