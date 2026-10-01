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
    runs = {"ACT": "act_cube_500", "OpenVLA": "openvla_spatial_500", "SmolVLA": "smolvla_hfvla_500",
            "π0.5": "pi05_spatial_500", "π0": "pi0_spatial_500", "Diffusion Policy": "dp_pusht_500"}
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
    raw = {("OpenVLA", "normal"): per_task("openvla_spatial_500", 10), ("SmolVLA", "normal"): per_task("smolvla_hfvla_500", 10),
           ("SmolVLA", "black"): per_task("smolvla_black_all"), ("π0", "normal"): per_task("pi0_spatial_500", 10),
           ("π0", "black"): per_task("pi0_black_all"), ("π0.5", "normal"): per_task("pi05_spatial_500", 10),
           ("π0.5", "black"): per_task("pi05_black_all")}
    rs = rows("blackout_per_task.csv")
    assert len(rs) == 8  # 4 个模型 × 正常 / 全涂黑;OpenVLA 全涂黑的原始日志不在仓库里,只核对其余 7 行
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
    key = {"π0": ("pi0_spatial_500", "pi0", "pi0_black_all"), "π0.5": ("pi05_spatial_500", "pi05", "pi05_black_all"),
           "SmolVLA": ("smolvla_hfvla_500", "smol", "smolvla_black_all")}
    rs = rows("perturbations.csv")
    assert {r["model"] for r in rs} == set(key)
    for r in rs:
        base, k, black = key[r["model"]]
        assert int(r["normal"]) == sum(per_task(base, 10))
        assert int(r["noise"]) == sum(per_task(f"pert_{k}_noise"))
        assert int(r["freeze"]) == sum(per_task(f"pert_{k}_freeze"))
        assert int(r["all_black"]) == sum(per_task(black))
        line = f"| {r['model']} | " + " | ".join(f"{r[c]}%" for c in ("normal", "noise", "freeze", "agent_black", "wrist_black", "all_black")) + " |"
        assert all(line in md for md in READMES), line


def test_finetune_csv_matches_raw_eval_info():
    rs = {r["model"]: r for r in rows("finetune_statedrop.csv")}
    for name, run in (("finetuned_control", "eval_ft_p0"), ("finetuned_state_zeroing", "eval_ft_p05")):
        assert int(rs[name]["normal"]) == sum(per_task(f"{run}_normal"))
        assert int(rs[name]["all_black"]) == sum(per_task(f"{run}_black"))
    assert (int(rs["original"]["normal"]), int(rs["original"]["all_black"])) == (sum(per_task("pi0_spatial_500", 10)), sum(per_task("pi0_black_all")))
    # README 2.4 的"额外下降":对照组 17、置零组 28
    drop = {k: int(r["normal"]) - int(r["all_black"]) for k, r in rs.items()}
    assert (drop["finetuned_control"], drop["finetuned_state_zeroing"]) == (17, 28)


def test_trajectory_summary_numbers_in_readme():
    """README 2.3 的分层数字:全涂黑仍成功的 7 个任务、失败的 3 个任务、任务 4–9 的噪声底线。"""
    t = {(r["metric"], r["pair"]): [float(r[f"task{i}"]) for i in range(10)] for r in rows("trajectory.csv")}
    succ = t["successes", "pi0_all_black"]
    ok = [i for i in range(10) if succ[i] >= 5]
    assert ok == [0, 1, 2, 3, 4, 6, 8] and sum(succ) == 54
    mean = lambda metric, pair, idx: sum(t[metric, pair][i] for i in idx) / len(idx)
    assert mean("path_dtw_cm", "pi0_all_black_vs_normal", ok) == pytest.approx(2.8, abs=0.05)
    assert mean("grasp_distance_cm", "pi0_all_black_vs_normal", ok) == pytest.approx(2.4, abs=0.05)
    assert mean("path_dtw_cm", "pi05_vs_pi0_normal", ok) == pytest.approx(2.9, abs=0.05)
    assert mean("grasp_distance_cm", "pi05_vs_pi0_normal", ok) == pytest.approx(2.6, abs=0.05)
    assert mean("path_dtw_cm", "pi0_normal_vs_rerun", range(4, 10)) == pytest.approx(3.4, abs=0.05)
    assert mean("grasp_distance_cm", "pi0_normal_vs_rerun", range(4, 10)) == pytest.approx(2.4, abs=0.05)
    assert max(t["path_dtw_cm", "pi0_normal_vs_rerun"][:4]) <= 0.3
    assert all(6 <= t["path_dtw_cm", "pi0_all_black_vs_normal"][i] <= 11 for i in (5, 7, 9))
    spread = json.loads((DATA / "traj_analyze.json").read_text())["grasp_spread"]["traj_pi0_normal"]
    assert sum(spread) / 10 == pytest.approx(1.8, abs=0.05)


def test_no_placeholder_left():
    for md in READMES:
        assert "running" not in md and "在跑" not in md
