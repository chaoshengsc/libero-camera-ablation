"""仓库里的派生结果必须能从原始评测 JSON 重算出来。"""
import csv
import json
from pathlib import Path

from metrics import ci95

ROOT = Path(__file__).resolve().parents[1]


def test_reproduction_csv_matches_raw_eval_info():
    runs = {"ACT": "act_cube_500", "OpenVLA": "openvla_spatial_500", "SmolVLA": "smolvla_hfvla_500",
            "π0.5": "pi05_spatial_500", "π0": "pi0_spatial_500", "Diffusion Policy": "dp_pusht_500"}
    rows = list(csv.DictReader(open(ROOT / "results" / "reproduction.csv")))
    assert {r["model"] for r in rows} == set(runs)
    for r in rows:
        info = json.loads((ROOT / "dashboard" / "data" / runs[r["model"]] / "eval_info.json").read_text())
        succ = [s for t in info["per_task"] for s in t["metrics"]["successes"]]
        pc = 100 * sum(succ) / len(succ)
        assert len(succ) == int(r["episodes"]) == 500
        assert round(pc, 1) == float(r["success_pc"])
        assert round(ci95(pc, len(succ)), 1) == float(r["ci95"])


def test_blackout_totals_match_per_task():
    for r in csv.DictReader(open(ROOT / "results" / "blackout_per_task.csv")):
        assert sum(int(r[f"task{i}"]) for i in range(10)) == int(r["total"])
