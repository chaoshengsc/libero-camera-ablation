"""P1/P2 source integrity, grouped statistics and target-shaped failure checks."""

import copy
import csv
import json
import shutil
from pathlib import Path

import numpy as np
import pytest
from summarize_followup import (
    DATA,
    load_replay_holdout,
    load_state_feedback,
    replay_statistics,
    sha,
    state_bootstrap,
)

ROOT = Path(__file__).resolve().parents[1]


def test_state_feedback_rebuilds_audited_statistics():
    y, episodes, runs, _ = load_state_feedback()
    assert len(episodes) == 1240
    assert sum(e["stage"] != "smoke" for e in episodes) == 1200
    assert [[r["successes"] for r in runs if r["group"] == group and r["stage"] != "smoke"]
            for group in "ABCD"] == [[72, 72, 76], [54, 54, 58], [0, 0, 0], [0, 0, 0]]
    point, rows = state_bootstrap(y)
    np.testing.assert_allclose(point, [73.3333333333, 55.3333333333, 0, 0])
    np.testing.assert_allclose([[r["difference_pp"], r["ci95_lo"], r["ci95_hi"]] for r in rows],
                               [[55.3333333333, 50, 60.3333333333],
                                [73.3333333333, 67.6666666667, 78.6666666667], [-18, -23, -13]])


def test_bootstrap_retains_tasks_and_whole_states():
    # Constant within each task, with distinct repeat/group patterns: resampling
    # whole states must not invent variance by mixing tasks, repeats or groups.
    y = np.zeros((10, 10, 3, 4), dtype=int)
    y[:5, :, :, 0] = 1
    y[:, :, 0, 1] = 1
    y[:, :, 1, 2] = 1
    _, rows = state_bootstrap(y)
    for row in rows:
        assert row["ci95_lo"] == pytest.approx(row["difference_pp"])
        assert row["ci95_hi"] == pytest.approx(row["difference_pp"])


def update_hash(directory, relative):
    path = directory / "metadata.json"
    metadata = json.loads(path.read_text())
    metadata["files"][relative] = sha(directory / relative)
    path.write_text(json.dumps(metadata))


@pytest.mark.parametrize("failure", ["unpaired", "missing"])
def test_state_pairing_rejects_semantically_bad_source(tmp_path, failure):
    directory = tmp_path / "state_feedback"
    shutil.copytree(DATA / "state_feedback", directory)
    relative = "r0_B/pairing.json"
    path = directory / relative
    pairing = json.loads(path.read_text())
    if failure == "unpaired":
        pairing["episodes"][0]["first_frame_hash"] = "different initial image"
    else:
        pairing["episodes"].pop()
    path.write_text(json.dumps(pairing))
    update_hash(directory, relative)  # Rehashing alone must not make bad evidence valid.
    with pytest.raises(AssertionError):
        load_state_feedback(directory)


def test_holdout_rebuilds_audited_statistics_and_sources():
    selection, outcomes, _ = load_replay_holdout()
    rows = replay_statistics(outcomes, selection)
    assert sum(r["success"] for r in outcomes["self"]) == 10
    assert [r["successes"] for r in rows[:-1]] == [32, 20, 26, 30, 30, 33, 29, 19, 17, 26]
    np.testing.assert_allclose([rows[-1][k] for k in ["successes", "episodes", "success_pc", "ci95_lo", "ci95_hi"]],
                               [262, 400, 65.5, 61, 69.75])
    assert {r["reason"] for r in outcomes["formal"]} == {"success", "sequence_exhausted"}


@pytest.mark.parametrize("failure", ["duplicate", "selection_leak", "changed_action", "invalid"])
def test_holdout_rejects_bad_targets_and_actions(tmp_path, failure):
    directory = tmp_path / "replay_holdout"
    shutil.copytree(DATA / "replay_holdout", directory)
    name = "source_actions.json" if failure == "changed_action" else "outcomes.json"
    path = directory / name
    data = json.loads(path.read_text())
    if failure == "duplicate":
        data["formal"][1] = copy.deepcopy(data["formal"][0])
    elif failure == "selection_leak":
        data["formal"][0]["target"] = 0
    elif failure == "changed_action":
        data["actions"]["0"][0][0] += 0.01
    else:
        data["invalid"].append({"task": 0, "target": 10, "error": "simulation failure"})
    path.write_text(json.dumps(data))
    update_hash(directory, name)
    with pytest.raises(AssertionError):
        load_replay_holdout(directory)


def test_followup_numbers_in_bilingual_reports():
    for name in ["README.md", "README_CN.md", "docs/EXPERIMENTS.md", "docs/EXPERIMENTS_CN.md"]:
        text = (ROOT / name).read_text()
        for value in ["262/400", "65.5%", "61.0–69.8%", "73.3%", "55.3%"]:
            assert value in text, (name, value)


def test_dashboard_followups_match_source_outcomes_and_intervals():
    text = (ROOT / "dashboard/followup.js").read_text()
    payload = json.loads(text.removeprefix("window.FOLLOWUP_RESULTS = ").strip().removesuffix(";"))
    _, episodes, runs, _ = load_state_feedback()
    formal = [e for e in episodes if e["stage"] != "smoke"]
    p1 = payload["p1"]
    assert p1["initial_states"] == len({(e["task"], e["initial"]) for e in formal}) == 100
    assert p1["repeats"] == len({e["repeat"] for e in formal}) == 3
    assert p1["formal_episodes"] == len(formal) == 1200
    assert p1["smoke_episodes"] == len(episodes) - len(formal) == 40
    rates = {g: 100 * sum(e["success"] for e in formal if e["group"] == g) / sum(e["group"] == g for e in formal) for g in "ABCD"}
    assert p1["rates"] == pytest.approx(rates)
    with (ROOT / "results/state_feedback_comparisons.csv").open() as stream:
        primary = next(row for row in csv.DictReader(stream) if row["role"] == "primary")
    assert p1["primary"]["comparison"] == primary["comparison"]
    for key in ("difference_pp", "ci95_lo", "ci95_hi"):
        assert p1["primary"][key] == pytest.approx(float(primary[key]))
    selection, outcomes, _ = load_replay_holdout()
    p2 = payload["p2"]
    assert p2["episodes"] == len(outcomes["formal"]) == 400
    assert p2["successes"] == sum(r["success"] for r in outcomes["formal"]) == 262
    assert p2["success_pc"] == 100 * p2["successes"] / p2["episodes"]
    assert p2["self_episodes"] == len(outcomes["self"]) == 10
    assert p2["self_successes"] == sum(r["success"] for r in outcomes["self"]) == 10
    assert p2["task_count"] == len(selection["tasks"]) == 10
    with (ROOT / "results/replay_holdout_summary.csv").open() as stream:
        total = next(row for row in csv.DictReader(stream) if row["task"] == "all")
    for key in ("ci95_lo", "ci95_hi"):
        assert p2[key] == pytest.approx(float(total[key]))
