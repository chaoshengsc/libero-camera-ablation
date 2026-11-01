"""Convert OpenVLA logs without replacing existing outputs.

Usage: ovla_to_json.py [run_name] [novideo] [--log FILE] [--output NEW_DIRECTORY]
No policy or simulator is imported. Failed output directories are retained.
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path


def run_name(value):
    if value in {".", ".."} or not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
        raise argparse.ArgumentTypeError("run_name must be a simple identifier, not a path")
    return value


def parse_log(text):
    """Keep each Task/video/Success block together; reject incomplete episodes."""
    tasks = {}
    task = video = None
    for line in text.splitlines():
        if line.startswith("Caught exception:"):
            raise ValueError("Log contains a simulation exception; retain and review the failed run")
        if line.startswith("Task:"):
            if task is not None:
                raise ValueError("Incomplete episode before the next Task record")
            task, video = line.removeprefix("Task:").strip(), None
            if not task:
                raise ValueError("Empty Task record")
        elif line.startswith("Saved rollout MP4 at path "):
            if task is None or video is not None:
                raise ValueError("Video record without a unique active episode")
            video = line.removeprefix("Saved rollout MP4 at path ").strip()
        elif line.startswith("Success:"):
            outcome = line.removeprefix("Success:").strip()
            if task is None or not video or outcome not in {"True", "False"}:
                raise ValueError("Invalid or incomplete Task/video/Success block")
            tasks.setdefault(task, []).append((video, outcome == "True"))
            task = video = None
    if task is not None or not tasks:
        raise ValueError("Log has no complete episodes or ends with an incomplete episode")
    return tasks


def convert(work, output, log, novideo):
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Output already exists; use --output with an unused directory: {output}")
    if log is None:
        logs = sorted((work / "logs").glob("*.txt"))
        if len(logs) != 1:
            raise ValueError(f"Expected exactly one input log, found {len(logs)}; select one with --log")
        log = logs[0]
    tasks = parse_log(log.read_text())
    per_task, copies = [], []
    for tid, (description, episodes) in enumerate(tasks.items()):
        videos = []
        if not novideo:
            for success in (True, False):
                index = next((i for i, (_, ok) in enumerate(episodes) if ok == success), None)
                if index is None:
                    continue
                source = Path(episodes[index][0])
                if not source.is_absolute():
                    source = work / source
                if not source.is_file():
                    raise FileNotFoundError(f"Selected video is missing: {source}; use novideo to omit video copies")
                relative = f"videos/task{tid}_{'ok' if success else 'fail'}.mp4"
                copies.append((source, relative))
                videos.append({"src": relative, "ep": index, "success": success})
        per_task.append({"task_group": "libero_spatial", "task_id": tid, "task": description,
                         "metrics": {"successes": [ok for _, ok in episodes]}, "videos": videos})
    outcomes = [ok for task in per_task for ok in task["metrics"]["successes"]]
    data = {"overall": {"pc_success": 100 * sum(outcomes) / len(outcomes), "n_episodes": len(outcomes)}, "per_task": per_task}
    serialized = json.dumps(data, ensure_ascii=False, indent=1, allow_nan=False)
    # Validate all inputs first, then atomically reserve a new output. Never clean old/failed outputs.
    output.mkdir(parents=True, exist_ok=False)
    if copies:
        (output / "videos").mkdir()
    for source, relative in copies:
        shutil.copyfile(source, output / relative)
    # Write the result last; a failed video copy must not publish a successful result JSON.
    with (output / "eval_info.json").open("x") as result:
        result.write(serialized)
    print("episodes", len(outcomes), "success", sum(outcomes), "videos", len(copies), "output", output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", nargs="?", default="openvla_spatial_500", type=run_name)
    parser.add_argument("mode", nargs="?", choices=["novideo"])
    parser.add_argument("--log", type=Path, help="Explicit input log when the run has more than one")
    parser.add_argument("--output", type=Path, help="Unused output directory; defaults to <run>/dash")
    args = parser.parse_args(argv)
    if not os.environ.get("EMB_ROOT"):
        parser.error("set EMB_ROOT to the configured working directory")
    work = Path(os.environ["EMB_ROOT"]) / "logs/eval" / args.run
    try:
        convert(work, args.output if args.output is not None else work / "dash", args.log, args.mode == "novideo")
    except (OSError, ValueError) as error:
        print(f"{args.run}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
