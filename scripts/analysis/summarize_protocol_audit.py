"""Recount existing LIBERO outcomes at a 220-control-step deadline; no rollout.

Default: check the managed CSV. --write regenerates that CSV after validation.
Raw NPZ/video evidence remains outside Git; this checks the published audit export.
"""

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "dashboard/data"
AUDIT = DATA / "protocol_audit"
OUTPUT = ROOT / "results/budget_sensitivity.csv"
FIELDS = ["run", "scope", "source_episodes", "episodes", "original_budget", "original_successes",
          "successes_by_220", "success_pc_by_220", "late_successes"]
PARTIAL = {"pi0_spatial_500", "pi05_spatial_500", "smolvla2_spatial_500"}
MATCHED = {"openvla_spatial_500", "official_pi0/ojx_none"}
COLUMNS = ["task", "initial", "steps", "action_count", "eef_count", "video_frames"]
NON_LIBERO = {"act_cube_500": 400, "dp_pusht_500": 300}
OPENVLA = {"openvla_spatial_500", "openvla_black_all", "run2/openvla_black_all"}
EVALUATOR_SHA = "fddec10c709401dd863814091d525fcd54d41cc6ccf51f7ef8300459cf69b873"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_metadata(record, episodes):
    """Validate recorded associations; raw external files cannot be rehashed here."""
    run = record["id"]
    if run in OPENVLA:
        kind = "ordered_original_task_video_success_blocks"
        hashes, paths = ["source_log_sha256", "parser_sha256"], [record.get("source_log_path")]
        require(record.get("caught_exceptions") == 0, f"Original parser exceptions: {run}")
    elif run.startswith("state_feedback/"):
        kind = "hash_bound_original_P1_evidence_and_local_NPZ"
        hashes, paths = ["source_evidence_sha256", "traj_sha256"], []
        require(record.get("video_checked") == episodes and record.get("video_action_mismatches") == 0,
                f"Incomplete P1 length association: {run}")
        require(record.get("image_tensor_saved") is False and record.get("stepwise_terminal_flags_saved") is False,
                f"Unexpected claim of recovered P1 fields: {run}")
    else:
        kind = "canonical_json_after_EMB_ROOT_replacement"
        hashes, paths = ["source_eval_sha256", "log_sha256"], record.get("canonical_matches")
        require(isinstance(paths, list) and paths, f"Missing canonical source locations: {run}")
    require(record.get("association") == kind, f"Missing/incorrect source association: {run}")
    for field in hashes + ["public_eval_sha256"] + (["traj_sha256"] if "traj_sha256" in record else []):
        value = record.get(field)
        require(isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value),
                f"Invalid/missing source hash: {run} {field}")
    for path in paths:
        require(isinstance(path, str) and path and not Path(path).is_absolute() and ".." not in Path(path).parts,
                f"Invalid/missing original source location: {run}")
    if "total_episodes" in record:
        require(record["total_episodes"] == episodes, f"Original episode count differs: {run}")


def summary(run, keys, label, outcomes, steps, budget):
    original = sum(outcomes[k] for k in keys)
    within = sum(outcomes[k] and (budget == 220 or steps[k] <= 220) for k in keys)
    return dict(zip(FIELDS, [run, label, len(outcomes), len(keys), budget, original,
                            within, round(100 * within / len(keys), 6), original - within], strict=True))


def audit_rows(directory=AUDIT, data=DATA):
    provenance = json.loads((directory / "provenance.json").read_text())
    lengths = json.loads((directory / "episode_lengths.json").read_text())
    require(provenance["schema"] == lengths["schema"] == 1, "Unsupported evidence schema")
    require(hashlib.sha256((directory / "episode_lengths.json").read_bytes()).hexdigest() == provenance["episode_lengths_sha256"],
            "Changed duration export")
    require(lengths["columns"] == COLUMNS, "Unexpected duration columns")
    require(provenance.get("evaluator_source_sha256") == EVALUATOR_SHA, "Missing/changed evaluator source")
    mapping = provenance.get("step_mapping", {})
    require(isinstance(mapping, dict), "Invalid control-step mapping metadata")
    for key in ("method", "limitations"):
        require(isinstance(mapping.get(key), str) and mapping[key], f"Missing step-mapping {key}")
    for key, count in {"old_trace_video_pairs": 6110, "old_action_video_pairs": 100,
                       "P1_action_video_pairs": 1240, "length_mismatches": 0}.items():
        require(type(mapping.get(key)) is int and mapping[key] == count, f"Missing/changed step-mapping count: {key}")
    records, durations = provenance["runs"], lengths["runs"]
    require(len(records) == 95 and len({r["id"] for r in records}) == 95, "Incomplete/duplicate frozen run inventory")
    require(len({r["id"] for r in durations}) == len(durations), "Duplicate duration run")
    index = {r["id"]: r["episodes"] for r in durations}
    require(set(index) == {r["id"] for r in records} - NON_LIBERO.keys() - OPENVLA,
            "Incomplete/unknown duration run inventory")
    rows = []
    for record in records:
        run = record["id"]
        require(run and ".." not in Path(run).parts and not Path(run).is_absolute(), "Invalid run identifier")
        path = data / run / "eval_info.json"
        require(hashlib.sha256(path.read_bytes()).hexdigest() == record["public_eval_sha256"], f"Changed source: {run}")
        source = json.loads(path.read_text())
        source_metadata(record, source["overall"]["n_episodes"])
        expected = NON_LIBERO.get(run, 220 if run in OPENVLA else 280)
        require(record["budget"] == [expected] and type(record["budget"][0]) is int,
                f"Unexpected original budget: {run}")
        if run in NON_LIBERO:
            continue
        tasks = source["per_task"]
        require(all(t["task_group"] == "libero_spatial" for t in tasks), f"Unexpected suite: {run}")
        require({int(t["task_id"]) for t in tasks} == set(range(10)) and len(tasks) == 10,
                f"Incomplete task coverage: {run}")
        outcomes = {(int(t["task_id"]), initial): bool(success) for t in tasks
                    for initial, success in enumerate(t["metrics"]["successes"])}
        require(len(outcomes) == source["overall"]["n_episodes"], f"Incomplete outcomes: {run}")
        budget = record["budget"][0]
        steps = {}
        if budget == 280:
            require(run in index, f"Missing durations: {run}")
            for task, initial, count, actions, eef, frames in index[run]:
                require(type(task) is int and type(initial) is int, f"Invalid episode identity: {run}")
                key = (task, initial)
                require(key not in steps and key in outcomes, f"Duplicate/unknown episode: {run} {key}")
                witnesses = [v for v in (actions, eef, frames) if v is not None]
                require(type(count) is int and 0 < count <= budget, f"Invalid duration: {run} {key}")
                require(witnesses and all(type(v) is int and v == count for v in witnesses),
                        f"Inconsistent recorded lengths: {run} {key}")
                steps[key] = count
            scope = "all"
            if set(steps) != set(outcomes):
                expected = {(task, initial) for task in range(10) for initial in range(10)}
                require(run in PARTIAL and set(steps) == expected and len(outcomes) == 500,
                        f"Incomplete duration coverage: {run}")
                scope = "matched100"
        else:
            require(run not in index, f"Unexpected inferred OpenVLA durations: {run}")
            steps = dict.fromkeys(outcomes, None)
            scope = "all"

        rows.append(summary(run, list(steps), scope, outcomes, steps, budget))
        if run in MATCHED:
            keys = [(task, initial) for task in range(10) for initial in range(10)]
            require(set(keys) <= set(steps), f"Missing matched subset: {run}")
            rows.append(summary(run, keys, "matched100", outcomes, steps, budget))
    return rows


def serialize(rows):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Regenerate the repository-managed CSV")
    args = parser.parse_args(argv)
    try:
        text = serialize(audit_rows())
        if args.write:
            OUTPUT.write_text(text)
        else:
            require(OUTPUT.read_text() == text, "Budget CSV differs; review the sources before using --write")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Protocol audit: {error}", file=sys.stderr)
        return 1
    print("Checked frozen run identities and recorded-trajectory deadline counts; no model or simulation was run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
