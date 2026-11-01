"""Offline layout checks must not silently ignore incomplete bundled assets."""

import importlib.util
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/checks/libero_assets_check.py"
spec = importlib.util.spec_from_file_location("libero_assets_check", SOURCE)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


@pytest.fixture
def layout(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "__init__.py").write_text('raise RuntimeError("must never import LIBERO")')
    for directory, suffix in [("bddl_files", ".bddl"), ("init_files", ".pruned_init")]:
        folder = package / directory / "libero_spatial"
        folder.mkdir(parents=True)
        for i in range(10):
            (folder / f"task{i}{suffix}").write_bytes(b"fixture")
    assets = tmp_path / "home/.cache/libero/assets"
    for name in checker.ASSET_DIRS:
        folder = assets / name
        folder.mkdir(parents=True)
        (folder / "mesh.xml").write_bytes(b"fixture")
    return package, tmp_path / "home", assets


def test_layout_uses_separate_home_cache_without_import(layout):
    package, home, assets = layout
    assert checker.check_assets(package, home) == assets


@pytest.mark.parametrize("failure", ["asset_missing", "asset_empty", "bddl_missing", "init_empty", "bundled_shadows_cache"])
def test_incomplete_layout_is_rejected(layout, failure):
    package, home, assets = layout
    if failure == "asset_missing":
        (assets / "scenes/mesh.xml").unlink()
        (assets / "scenes").rmdir()
    elif failure == "asset_empty": (assets / "scenes/mesh.xml").write_bytes(b"")
    elif failure == "bddl_missing": (package / "bddl_files/libero_spatial/task0.bddl").unlink()
    elif failure == "init_empty": (package / "init_files/libero_spatial/task0.pruned_init").write_bytes(b"")
    else: (package / "assets").mkdir()
    with pytest.raises(ValueError):
        checker.check_assets(package, home)
