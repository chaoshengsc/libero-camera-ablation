"""Summarize the original 500-normal/100-black runs after validating coverage.

Keep the first ten normal episodes per task; reject empty, incomplete or ambiguous
inputs. Outputs must be new paths. This is not a seed/hash pairing acceptance gate.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from ovla_to_json import parse_log
from summarize_eval import load_info

DATA = Path(__file__).resolve().parents[2] / "dashboard/data"


def one_file(paths, label):
    paths = sorted(paths)
    if len(paths) != 1:
        raise ValueError(f"{label}: expected exactly one input, found {len(paths)}")
    return paths[0]


def lerobot(root, run, first=None):
    path = one_file((root / run / "out").rglob("eval_info.json"), run)
    tasks = load_info(path)["per_task"]
    expected = 50 if first is not None else 10
    if len(tasks) != 10 or {t["task_id"] for t in tasks} != set(range(10)):
        raise ValueError(f"{run}: expected task ids 0 through 9")
    for task in tasks:
        if task.get("task_group") != "libero_spatial" or len(task["metrics"]["successes"]) != expected:
            raise ValueError(f"{run}: expected ten LIBERO-Spatial tasks with {expected} episodes each")
    return [sum(t["metrics"]["successes"][:first]) for t in sorted(tasks, key=lambda t: t["task_id"])]


def openvla(root, run, first=None):
    path = one_file((root / run / "logs").glob("*.txt"), run)
    tasks = parse_log(path.read_text())
    # Bind log descriptions to the frozen task-id order used by public tables.
    reference = load_info(DATA / "openvla_spatial_500/eval_info.json")["per_task"]
    names = [t["task"] for t in sorted(reference, key=lambda t: t["task_id"])]
    expected = 50 if first is not None else 10
    if set(tasks) != set(names) or any(len(values) != expected for values in tasks.values()):
        raise ValueError(f"{run}: expected ten known LIBERO-Spatial tasks with {expected} complete episodes each")
    return [sum(ok for _, ok in tasks[name][:first]) for name in names]


def summarize(root):
    rows = [("OpenVLA", openvla(root, "openvla_spatial_500", 10), openvla(root, "openvla_black_all"))]
    for model, normal, black in [("SmolVLA", "smolvla2_spatial_500", "smol2_black_all"),
                                  ("pi0", "pi0_spatial_500", "pi0_black_all"), ("pi0.5", "pi05_spatial_500", "pi05_black_all")]:
        rows.append((model, lerobot(root, normal, 10), lerobot(root, black)))
    return [{"model": model, "normal": normal, "black": black} for model, normal, black in rows]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Unused JSON path; defaults to $EMB_ROOT/logs/eval/B_summary.json")
    args = parser.parse_args(argv)
    if not os.environ.get("EMB_ROOT"):
        parser.error("set EMB_ROOT to the configured working directory")
    root = Path(os.environ["EMB_ROOT"]) / "logs/eval"
    output = args.output if args.output is not None else root / "B_summary.json"
    try:
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Output already exists; choose an unused --output: {output}")
        rows = summarize(root)
        text = json.dumps(rows, ensure_ascii=False, allow_nan=False)
        with output.open("x") as result:
            result.write(text)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Blackout summary: {error}", file=sys.stderr)
        return 1
    for row in rows:
        a, b = row["normal"], row["black"]
        print(f"{row['model']:8} normal {sum(a):3}/100  black {sum(b):3}/100  drop {sum(a) - sum(b):+d} points | normal {a} | black {b}")
    print("output", output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
