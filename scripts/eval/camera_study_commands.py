"""Print a selected camera-study command; never execute it, load models or write outputs."""

import argparse
import json
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "configs/camera_study_runs.json"


def build_command(manifest, run_id, new_run_name, emb_root, smoke=False):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", new_run_name) or new_run_name in {".", ".."}:
        raise ValueError("new run name must use letters, digits, underscore, dot or hyphen")
    row = next((row for row in manifest["runs"] if row["run_id"] == run_id), None)
    if row is None:
        raise ValueError("unknown historical run; use --list")
    if not emb_root.is_absolute():
        raise ValueError("--emb-root must be an absolute path on the target device")
    output = emb_root / "logs/eval" / new_run_name
    if output.exists() or output.is_symlink():
        raise ValueError("output already exists; choose a new run name")
    model = manifest["models"][row["model"]]
    recipe = manifest["continuation_recipe"]
    args = [
        "env",
        "-u",
        "POLICY_SERVER",
        "-u",
        "OPENPI_AUTHKEY",
        f"EMB_ROOT={emb_root}",
        f"WRAP={recipe['wrap']}",
        f"BLACKOUT={row['blackout']}",
        "DELTA_REF=chunk",
        "bash",
        str(ROOT / recipe["entry"]),
        new_run_name,
        str(1 if smoke else recipe["episodes_per_task"]),
        str(emb_root / "ckpt" / model["local_checkpoint_dir"]),
        str(recipe["batch_size"]),
        f"--policy.n_action_steps={model['n_action_steps']}",
        f"--policy.chunk_size={recipe['chunk_size']}",
        f"--policy.num_inference_steps={recipe['num_inference_steps']}",
        f"--env.observation_height={recipe['observation_height']}",
        f"--env.observation_width={recipe['observation_width']}",
        f"--env.episode_length={recipe['control_budget']}",
        f"--env.max_parallel_tasks={recipe['max_parallel_tasks']}",
    ]
    return shlex.join(args)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List the 11 recorded run templates")
    group.add_argument("--run", help="Historical run id, for example s500/pi05_drop_wrist")
    parser.add_argument("--new-run-name", help="New unused output name, never the historical output")
    parser.add_argument("--emb-root", type=Path, help="Prepared working directory on the target device")
    parser.add_argument("--smoke", action="store_true", help="Print one episode per task instead of 50; still executes nothing")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(MANIFEST.read_text())
        if args.list:
            for row in manifest["runs"]:
                print(f"{row['run_id']}\tBLACKOUT={row['blackout']}\tanalysis normal={row['analysis_normal_run']}")
            return 0
        if not args.new_run_name or args.emb_root is None:
            parser.error("--run requires --new-run-name and --emb-root")
        print("Prepared command only; environment, assets and target-device runtime remain unverified.", file=sys.stderr)
        print("Width=360 and budget=280 are explicit new-run settings, not a recovered historical CLI.", file=sys.stderr)
        print("Collect a new normal control on the target device. Review the command before running it.", file=sys.stderr)
        print(build_command(manifest, args.run, args.new_run_name, args.emb_root, args.smoke))
    except (OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
