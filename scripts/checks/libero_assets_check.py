"""Check hf-libero 0.1.4's asset layout without importing LIBERO or a simulator."""

import argparse
import sys
from importlib import metadata
from pathlib import Path

ASSET_DIRS = ("articulated_objects", "stable_scanned_objects", "turbosquid_objects", "stable_hope_objects", "scenes")


def check_assets(package, home):
    if not (package / "__init__.py").is_file():
        raise ValueError(f"Missing hf-libero package files: {package}")
    for directory, pattern in [("bddl_files/libero_spatial", "*.bddl"), ("init_files/libero_spatial", "*.pruned_init")]:
        files = list((package / directory).glob(pattern))
        if len(files) != 10 or any(not p.is_file() or p.stat().st_size == 0 for p in files):
            raise ValueError(f"Expected ten nonempty Spatial task files: {package / directory}")
    # Match get_assets_path(): packaged assets take priority, even if incomplete.
    bundled = package / "assets"
    assets = bundled if bundled.exists() else home / ".cache/libero/assets"
    for name in ASSET_DIRS:
        directory = assets / name
        if not directory.is_dir() or not any(p.is_file() and p.stat().st_size for p in directory.rglob("*")):
            raise ValueError(f"Missing/empty asset directory: {directory}")
    return assets


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        dist = metadata.distribution("hf-libero")
        if dist.version != "0.1.4":
            raise ValueError(f"Expected hf-libero 0.1.4, found {dist.version}")
        package = Path(dist.locate_file("libero/libero"))
        assets = check_assets(package, Path.home())
    except (metadata.PackageNotFoundError, OSError, ValueError) as error:
        print(f"LIBERO assets: {error}", file=sys.stderr)
        return 1
    print(f"LIBERO Spatial files and required asset directories present: {assets}")
    print("Layout check only; no download, LIBERO import, rendering or content-hash acceptance")
    return 0


if __name__ == "__main__":
    sys.exit(main())
