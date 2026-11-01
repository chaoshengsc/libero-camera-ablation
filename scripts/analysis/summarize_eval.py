"""Summarize result JSONs; any missing, ambiguous or invalid input returns nonzero.

Usage: summarize_eval.py RUN [RUN ...] | summarize_eval.py --file eval_info.json
Intervals retain the historical binomial normal approximation. This is not a run-acceptance gate.
"""

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path


def run_name(value):
    if value in {".", ".."} or not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
        raise argparse.ArgumentTypeError("run_name must be a simple identifier, not a path")
    return value


def finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be finite and numeric")
    return value


def load_info(path):
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or not isinstance(data.get("overall"), dict) or not isinstance(data.get("per_task"), list) or not data["per_task"]:
        raise ValueError("Expected overall and nonempty per_task records")
    overall, tasks = data["overall"], data["per_task"]
    n = overall.get("n_episodes")
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise ValueError("n_episodes must be a positive integer")
    pc = finite_number(overall.get("pc_success"), "pc_success")
    if not 0 <= pc <= 100:
        raise ValueError("pc_success must lie between 0 and 100")
    outcomes, ids = [], set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict) or not isinstance(task.get("metrics"), dict):
            raise ValueError("Expected per-task metrics")
        tid = task.get("task_id", index)
        if isinstance(tid, bool) or not isinstance(tid, int) or tid < 0 or tid in ids:
            raise ValueError("Task ids must be distinct nonnegative integers")
        ids.add(tid)
        successes = task["metrics"].get("successes")
        if not isinstance(successes, list) or not successes or any(type(v) not in (bool, int) or v not in (0, 1) for v in successes):
            raise ValueError("Each task must contain nonempty boolean/0-or-1 successes")
        outcomes.extend(successes)
    if len(outcomes) != n or not math.isclose(pc, 100 * sum(outcomes) / n, abs_tol=0.051, rel_tol=1e-9):
        raise ValueError("Overall counts/rate disagree with per-task outcomes")
    for key in ("eval_ep_s", "avg_max_reward"):
        if overall.get(key) is not None:
            value = finite_number(overall[key], key)
            if key == "eval_ep_s" and value < 0:
                raise ValueError("eval_ep_s must be nonnegative")
    return data


def summarize(label, path):
    data = load_info(path)
    overall, tasks = data["overall"], data["per_task"]
    pc, n = overall["pc_success"], overall["n_episodes"]
    ci = 196 * math.sqrt(pc / 100 * (1 - pc / 100) / n)
    extra = f"  avg_max_reward={overall['avg_max_reward']:.3f}" if "pusht" in label and overall.get("avg_max_reward") is not None else ""
    timing = f"  {overall['eval_ep_s']:.1f}s per episode" if overall.get("eval_ep_s") is not None else ""
    print(f"== {label}: {pc:.1f}%  (n={n}, 95%CI ±{ci:.1f}){extra}{timing}")
    if len(tasks) > 1:
        print("   per task:", " ".join(f"{sum(t['metrics']['successes'])}/{len(t['metrics']['successes'])}" for t in tasks))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="*", type=run_name)
    parser.add_argument("--file", type=Path, help="Read one explicit JSON instead of searching run directories")
    args = parser.parse_args(argv)
    if bool(args.runs) == (args.file is not None):
        parser.error("supply RUN names or --file, but not both")
    if args.runs and not os.environ.get("EMB_ROOT"):
        parser.error("set EMB_ROOT to the configured working directory")
    inputs = [(str(args.file), args.file)] if args.file is not None else [(name, None) for name in args.runs]
    status = 0
    for label, path in inputs:
        try:
            if path is None:
                matches = sorted((Path(os.environ["EMB_ROOT"]) / "logs/eval" / label).rglob("eval_info.json"))
                if len(matches) != 1:
                    raise ValueError(f"Expected exactly one eval_info.json, found {len(matches)}; select one with --file")
                path = matches[0]
            summarize(label, path)
        except (OSError, ValueError) as error:
            print(f"{label}: {error}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
