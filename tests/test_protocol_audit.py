"""Recorded deadlines must retain episode coverage and the original denominators."""

import hashlib
import json
import shutil

import pytest
from summarize_protocol_audit import AUDIT, audit_rows, serialize


def write_evidence(directory, data):
    path = directory / "episode_lengths.json"
    path.write_text(json.dumps(data))
    meta = directory / "provenance.json"
    provenance = json.loads(meta.read_text())
    provenance["episode_lengths_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    meta.write_text(json.dumps(provenance))


def test_existing_headlines_and_official_gate_at_common_deadline():
    rows = {(r["run"], r["scope"]): r for r in audit_rows()}
    for run, normal in [("pi0_spatial_500", 76), ("pi05_spatial_500", 99),
                        ("smolvla2_spatial_500", 83), ("openvla_spatial_500", 81)]:
        row = rows[run, "matched100"]
        assert row["episodes"] == 100 and row["source_episodes"] == 500
        assert row["original_successes"] == row["successes_by_220"] == normal
    for run, success in [("pi0_black_all", 56), ("pi05_black_all", 0), ("smol2_black_all", 0), ("openvla_black_all", 0)]:
        assert rows[run, "all"]["successes_by_220"] == success
    gate = rows["official_pi0/ojx_none", "all"]
    assert (gate["episodes"], gate["original_successes"], gate["successes_by_220"]) == (500, 482, 481)
    assert rows["official_pi0/ojx_all", "all"]["successes_by_220"] == 0
    assert rows["s500/pi0_none", "all"]["successes_by_220"] == 359
    assert all(r["original_successes"] - r["successes_by_220"] == r["late_successes"] >= 0 for r in rows.values())


@pytest.mark.parametrize("failure", ["duplicate", "missing", "disagree", "over_budget", "unknown_run", "missing_run", "bool_identity"])
def test_malformed_evidence_cannot_pass_with_same_source_hashes(tmp_path, failure):
    directory = tmp_path / "audit"
    shutil.copytree(AUDIT, directory)
    path = directory / "episode_lengths.json"
    data = json.loads(path.read_text())
    target = next(r for r in data["runs"] if r["id"] == "official_pi0/ojx_none")
    if failure == "duplicate":
        target["episodes"][1] = target["episodes"][0].copy()
    elif failure == "missing":
        target["episodes"].pop()
    elif failure == "disagree":
        target["episodes"][0][-1] += 1
    elif failure == "over_budget":
        target["episodes"][0][2:] = [281, None, 281, None]
    elif failure == "unknown_run":
        data["runs"][0]["id"] = "unregistered"
    elif failure == "bool_identity":
        target["episodes"][0][0] = False
    else:
        data["runs"].remove(target)
    write_evidence(directory, data)  # Consistent hashes cannot hide semantic errors.
    with pytest.raises(ValueError):
        audit_rows(directory)


def test_camera_run_cannot_be_silently_excluded_as_another_environment(tmp_path):
    directory = tmp_path / "audit"
    shutil.copytree(AUDIT, directory)
    path = directory / "provenance.json"
    data = json.loads(path.read_text())
    next(r for r in data["runs"] if r["id"] == "pi0_spatial_500")["budget"] = [400]
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        audit_rows(directory)


def test_280_step_run_cannot_skip_duration_check_by_claiming_220(tmp_path):
    directory = tmp_path / "audit"
    shutil.copytree(AUDIT, directory)
    lengths = json.loads((directory / "episode_lengths.json").read_text())
    lengths["runs"] = [r for r in lengths["runs"] if r["id"] != "official_pi0/ojx_none"]
    write_evidence(directory, lengths)
    path = directory / "provenance.json"
    provenance = json.loads(path.read_text())
    next(r for r in provenance["runs"] if r["id"] == "official_pi0/ojx_none")["budget"] = [220]
    path.write_text(json.dumps(provenance))
    with pytest.raises(ValueError):
        audit_rows(directory)


@pytest.mark.parametrize("missing", ["all", "canonical", "openvla", "p1"])
def test_missing_original_association_evidence_is_rejected(tmp_path, missing):
    directory = tmp_path / "audit"
    shutil.copytree(AUDIT, directory)
    path = directory / "provenance.json"
    provenance = json.loads(path.read_text())
    if missing == "all":
        provenance.pop("evaluator_source_sha256")
        provenance.pop("step_mapping")
        for record in provenance["runs"]:
            record.pop("association")
    else:
        run, field = {"canonical": ("pi0_spatial_500", "source_eval_sha256"),
                      "openvla": ("openvla_spatial_500", "source_log_sha256"),
                      "p1": ("state_feedback/r0_A", "source_evidence_sha256")}[missing]
        next(r for r in provenance["runs"] if r["id"] == run).pop(field)
    path.write_text(json.dumps(provenance))
    with pytest.raises(ValueError):
        audit_rows(directory)


def test_deadline_boundary_is_inclusive_and_failures_stay_in_denominator(tmp_path):
    directory = tmp_path / "audit"
    shutil.copytree(AUDIT, directory)
    path = directory / "episode_lengths.json"
    data = json.loads(path.read_text())
    target = next(r for r in data["runs"] if r["id"] == "official_pi0/ojx_none")
    source = json.loads((AUDIT.parent / "official_pi0/ojx_none/eval_info.json").read_text())
    successes = {(t["task_id"], i) for t in source["per_task"] for i, ok in enumerate(t["metrics"]["successes"]) if ok}
    episode = next(e for e in target["episodes"] if (e[0], e[1]) in successes)
    original = [e.copy() for e in target["episodes"]]
    results = []
    for count in (220, 221):
        episode[2:] = [count, None, count, None]
        write_evidence(directory, data)
        row = next(r for r in audit_rows(directory) if r["run"] == target["id"] and r["scope"] == "all")
        results.append(row)
    assert results[0]["successes_by_220"] == results[1]["successes_by_220"] + 1
    assert results[0]["episodes"] == results[1]["episodes"] == len(original) == 500
    assert results[0]["original_successes"] == results[1]["original_successes"] == 482


def test_managed_csv_matches_validated_export():
    assert (AUDIT.parents[2] / "results/budget_sensitivity.csv").read_text() == serialize(audit_rows())
