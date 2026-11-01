"""Known-bad public links, versions and JS must fail the offline CI check."""

import importlib.util
import subprocess
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/checks/repository_check.py"
spec = importlib.util.spec_from_file_location("repository_check", SOURCE)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repository with spaces"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "docs").mkdir()
    (root / "dashboard").mkdir()
    for name in ["README.md", "README_CN.md"]:
        (root / name).write_text("# Home\nversion = {1.5.0}\n[guide](docs/guide.md#中文-heading-code)\n")
    (root / "pyproject.toml").write_text('[project]\nversion = "1.5.0"\n')
    (root / "CITATION.cff").write_text('version: "1.5.0"\n')
    (root / "docs/guide.md").write_text('''# 中文 Heading `code`
[home](../README.md#home)
[custom](#explicit)
[repeat](#repeat-1)
[site](../dashboard/index.html#main)
<a id="explicit"></a>
## Repeat
## Repeat
```markdown
[example](nonexistent.md)
```
`[code](also-absent.md)`
''')
    (root / "dashboard/index.html").write_text('<main id="main"><a href="../docs/guide.md#explicit">Guide</a></main>')
    (root / "dashboard/app.js").write_text("throw new Error('syntax checks must not execute this file');\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    return root


def test_good_repository_passes_without_executing_javascript(repository):
    assert checker.main(["--root", str(repository)]) == 0


@pytest.mark.parametrize("target", ["missing.md", "guide.md#missing", "../README.md#missing", "../../outside.md"])
def test_missing_target_or_fragment_is_rejected(repository, target):
    path = repository / "docs/guide.md"
    path.write_text(path.read_text() + f"\n[broken]({target})\n")
    errors, _ = checker.check_links(repository, checker.tracked_files(repository))
    assert errors and any(target in error for error in errors)
    assert checker.main(["--root", str(repository)]) == 1


def test_untracked_local_file_cannot_hide_a_broken_public_link(repository):
    (repository / "docs/local-only.md").write_text("private local note")
    path = repository / "docs/guide.md"
    path.write_text(path.read_text() + "\n[local](local-only.md)\n")
    errors, _ = checker.check_links(repository, checker.tracked_files(repository))
    assert any("local-only.md" in error for error in errors)


def test_html_images_and_srcset_are_checked(repository):
    path = repository / "dashboard/index.html"
    path.write_text('<main id="main"><img src="missing.svg"><source srcset="missing2.svg 2x"></main>')
    errors, _ = checker.check_links(repository, checker.tracked_files(repository))
    assert any("missing.svg" in error for error in errors)
    assert any("missing2.svg" in error for error in errors)


@pytest.mark.parametrize("name", ["pyproject.toml", "CITATION.cff", "README.md", "README_CN.md"])
def test_each_version_source_can_fail(repository, name):
    path = repository / name
    path.write_text(path.read_text().replace("1.5.0", "0.0.1"))
    assert checker.check_versions(repository)
    assert checker.main(["--root", str(repository)]) == 1


def test_missing_version_and_required_file_fail(repository):
    (repository / "README.md").write_text("# Home\n")
    assert checker.check_versions(repository)
    (repository / "CITATION.cff").unlink()
    assert checker.main(["--root", str(repository)]) == 1


def test_real_javascript_syntax_error_fails(repository):
    (repository / "dashboard/app.js").write_text("const broken = ;\n")
    errors, count = checker.check_javascript(checker.tracked_files(repository))
    assert count == 1 and errors
    assert checker.main(["--root", str(repository)]) == 1


def test_missing_node_is_a_failure_not_a_silent_skip(repository, monkeypatch):
    monkeypatch.setattr(checker.shutil, "which", lambda name: None)
    assert checker.main(["--root", str(repository)]) == 1


def test_invalid_repository_fails_without_traceback(tmp_path, capsys):
    assert checker.main(["--root", str(tmp_path)]) == 1
    assert "error:" in capsys.readouterr().err


def test_nested_badge_checks_both_image_and_outer_target(repository):
    image = repository / "docs/badge.svg"
    image.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    subprocess.run(["git", "-C", str(repository), "add", "docs/badge.svg"], check=True)
    readme = repository / "README.md"
    original = readme.read_text()
    readme.write_text(original + "\n[![Badge](docs/badge.svg)](MISSING_LICENSE)\n")
    errors, _ = checker.check_links(repository, checker.tracked_files(repository))
    assert any("MISSING_LICENSE" in error for error in errors)
    readme.write_text(original + "\n[![Badge](docs/missing.svg)](CITATION.cff)\n")
    errors, _ = checker.check_links(repository, checker.tracked_files(repository))
    assert any("docs/missing.svg" in error for error in errors)


@pytest.mark.parametrize("name", ["description", "viewport"])
def test_metadata_name_is_not_a_navigation_anchor(repository, name):
    page = repository / "dashboard/index.html"
    page.write_text(f'<meta name="{name}" content="test"><main id="main"><a name="legacy"></a></main>')
    readme = repository / "README.md"
    readme.write_text(readme.read_text() + f"\n[bad](dashboard/index.html#{name})\n[legacy](dashboard/index.html#legacy)\n")
    errors, _ = checker.check_links(repository, checker.tracked_files(repository))
    assert any(f"#{name}" in error for error in errors)
    assert not any("#legacy" in error for error in errors)
