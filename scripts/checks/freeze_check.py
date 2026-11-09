"""Verify the dated camera-ablation evidence manifest without writing files.

Run from any directory: python scripts/checks/freeze_check.py
Only listed public data/result files are checked. Private payloads and scientific
interpretations are not verified by a checksum. No model or network is used.
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "results/freeze_20261109.sha256"


def verify(root, manifest):
    records = manifest.read_text().splitlines()
    if not records:
        raise ValueError("empty freeze manifest")
    seen = set()
    for line in records:
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise ValueError("malformed freeze manifest entry")
        expected, name = match.groups()
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or str(relative) != name or name in seen:
            raise ValueError(f"invalid or duplicate evidence path: {name}")
        if not name.startswith(("dashboard/data/", "results/")) or name == "results/freeze_20261109.sha256":
            raise ValueError(f"path outside frozen evidence scope: {name}")
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError(f"missing or unsafe evidence file: {name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"frozen evidence changed: {name}")
        seen.add(name)
    if list(seen) and [line[66:] for line in records] != sorted(seen):
        raise ValueError("freeze manifest is not sorted")
    return len(seen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository to verify; defaults to this checkout")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        count = verify(root, root / MANIFEST.relative_to(ROOT))
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Verified {count} frozen public evidence files (v1.5.1, 2026-11-09); no model run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
