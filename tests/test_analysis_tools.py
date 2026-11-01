"""Run the result CLIs against small local fixtures; no policy or simulator."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from ovla_to_json import main as convert_main
from summarize_eval import load_info

ROOT = Path(__file__).resolve().parents[1]


def cli(script, emb, *args, **env):
    return subprocess.run([sys.executable, str(ROOT / "scripts/analysis" / script), *map(str, args)],
                          capture_output=True, text=True, timeout=10, env={**os.environ, "EMB_ROOT": str(emb), **env})


def episode(task, video, success):
    return f"\nTask: {task}\nStarting episode 1...\nSaved rollout MP4 at path {video}\nSuccess: {success}\n"


def make_log(emb):
    run = emb / "logs/eval/demo"
    (run / "logs").mkdir(parents=True)
    (run / "rollouts").mkdir()
    for name in ("a ok.mp4", "a fail.mp4", "b.mp4"):
        (run / "rollouts" / name).write_bytes(name.encode())
    text = episode("task A", "./rollouts/a ok.mp4", "True")
    text += episode("task A", "./rollouts/a fail.mp4", "False")
    text += episode("task B", run / "rollouts/b.mp4", "True")
    (run / "logs/eval.txt").write_text(text)
    return run


def make_info(emb, name="good"):
    path = emb / "logs/eval" / name / "out/eval_info.json"
    path.parent.mkdir(parents=True)
    data = {"overall": {"pc_success": 75.0, "n_episodes": 4, "eval_ep_s": 2.5},
            "per_task": [{"task_id": 0, "metrics": {"successes": [True, False]}},
                         {"task_id": 1, "metrics": {"successes": [True, True]}}]}
    path.write_text(json.dumps(data))
    return path, data


@pytest.mark.parametrize("existing", ["directory", "file", "symlink", "dangling_symlink"])
def test_converter_preserves_existing_output_even_without_input(tmp_path, existing):
    run = tmp_path / "logs/eval/demo"
    run.mkdir(parents=True)
    target = run / "dash"
    original = tmp_path / "original"
    original.mkdir()
    (original / "keep").write_bytes(b"original")
    if existing == "directory":
        target.mkdir()
        (target / "keep").write_bytes(b"original")
    elif existing == "file":
        target.write_bytes(b"original")
    else:
        target.symlink_to(original if existing == "symlink" else tmp_path / "absent")
    result = cli("ovla_to_json.py", tmp_path, "demo")
    assert result.returncode != 0
    assert (original / "keep").read_bytes() == b"original"
    if existing == "directory":
        assert list(target.iterdir()) == [target / "keep"]
        assert (target / "keep").read_bytes() == b"original"
    elif existing == "file":
        assert target.read_bytes() == b"original"
    else:
        assert target.is_symlink()


@pytest.mark.parametrize("failure", ["missing", "empty", "empty_task", "truncated", "bad_success", "missing_video", "exception", "ambiguous"])
def test_converter_rejects_bad_input_without_creating_output(tmp_path, failure):
    run = make_log(tmp_path)
    log = run / "logs/eval.txt"
    if failure == "missing":
        log.unlink()
    elif failure == "empty":
        log.write_text("Task suite: libero_spatial\n")
    elif failure == "empty_task":
        log.write_text(log.read_text() + "Task:\n")
    elif failure == "truncated":
        log.write_text(log.read_text() + "Task: task C\nStarting episode 1...\n")
    elif failure == "bad_success":
        log.write_text(log.read_text().replace("Success: True", "Success: unknown", 1))
    elif failure == "missing_video":
        (run / "rollouts/a ok.mp4").unlink()
    elif failure == "exception":
        log.write_text(log.read_text().replace("Success: False", "Caught exception: broken simulation\nSuccess: False"))
    else:
        (run / "logs/another.txt").write_text(log.read_text())
    result = cli("ovla_to_json.py", tmp_path, "demo")
    assert result.returncode != 0, result.stdout
    assert not (run / "dash").exists()


def test_converter_counts_and_copies_selected_videos_with_spaces(tmp_path):
    emb = tmp_path / "work directory"
    run = make_log(emb)
    result = cli("ovla_to_json.py", emb, "demo")
    assert result.returncode == 0, result.stderr
    out = run / "dash"
    data = json.loads((out / "eval_info.json").read_text())
    assert data["overall"] == {"pc_success": 200 / 3, "n_episodes": 3}
    assert [t["metrics"]["successes"] for t in data["per_task"]] == [[True, False], [True]]
    assert (out / "videos/task0_ok.mp4").read_bytes() == b"a ok.mp4"
    assert (out / "videos/task0_fail.mp4").read_bytes() == b"a fail.mp4"
    assert (out / "videos/task1_ok.mp4").read_bytes() == b"b.mp4"
    original = (out / "eval_info.json").read_bytes()
    assert cli("ovla_to_json.py", emb, "demo").returncode != 0
    assert (out / "eval_info.json").read_bytes() == original


def test_converter_novideo_and_explicit_log_output_preserve_old_dash(tmp_path):
    run = make_log(tmp_path)
    old = run / "dash"
    old.mkdir()
    (old / "keep").write_bytes(b"old")
    (run / "logs/other.txt").write_text("broken")
    for video in (run / "rollouts").iterdir():
        video.unlink()
    output = run / "dash_new"
    result = cli("ovla_to_json.py", tmp_path, "demo", "novideo", "--log", run / "logs/eval.txt", "--output", output)
    assert result.returncode == 0, result.stderr
    assert (old / "keep").read_bytes() == b"old"
    data = json.loads((output / "eval_info.json").read_text())
    assert data["overall"]["n_episodes"] == 3
    assert all(t["videos"] == [] for t in data["per_task"])


def test_converter_concurrent_starts_publish_only_one_output(tmp_path):
    run = make_log(tmp_path)
    command = [sys.executable, str(ROOT / "scripts/analysis/ovla_to_json.py"), "demo", "novideo"]
    processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={**os.environ, "EMB_ROOT": str(tmp_path)}) for _ in range(2)]
    for process in processes:
        process.communicate(timeout=10)
    assert sorted(p.returncode for p in processes) == [0, 1]
    assert json.loads((run / "dash/eval_info.json").read_text())["overall"]["n_episodes"] == 3


def test_converter_retains_failed_copy_without_publishing_result(tmp_path, monkeypatch):
    run = make_log(tmp_path)
    monkeypatch.setenv("EMB_ROOT", str(tmp_path))

    def failed_copy(source, target):
        Path(target).write_bytes(b"partial video")
        raise OSError("simulated full disk")

    monkeypatch.setattr("ovla_to_json.shutil.copyfile", failed_copy)
    assert convert_main(["demo"]) == 1
    assert (run / "dash/videos/task0_ok.mp4").read_bytes() == b"partial video"
    assert not (run / "dash/eval_info.json").exists()
    assert convert_main(["demo"]) == 1
    assert (run / "dash/videos/task0_ok.mp4").read_bytes() == b"partial video"


def test_summary_reports_missing_run_and_keeps_valid_summaries(tmp_path):
    make_info(tmp_path)
    result = cli("summarize_eval.py", tmp_path, "missing", "good")
    assert result.returncode == 1
    assert "missing" in result.stderr
    assert "good: 75.0%" in result.stdout
    assert "1/2 2/2" in result.stdout


@pytest.mark.parametrize("failure", ["json", "zero", "bad_percent", "nan", "coverage", "rate", "outcome", "duplicate_task", "timing", "ambiguous"])
def test_summary_rejects_invalid_or_ambiguous_results(tmp_path, failure):
    path, data = make_info(tmp_path)
    if failure == "json":
        path.write_text("{")
    elif failure == "ambiguous":
        other = path.parent.parent / "dash/eval_info.json"
        other.parent.mkdir()
        other.write_text(path.read_text())
    else:
        if failure == "zero":
            data["overall"]["n_episodes"] = 0
        elif failure == "bad_percent":
            data["overall"]["pc_success"] = 110
        elif failure == "nan":
            data["overall"]["pc_success"] = float("nan")
        elif failure == "coverage":
            data["overall"]["n_episodes"] = 5
        elif failure == "rate":
            data["overall"]["pc_success"] = 50
        elif failure == "outcome":
            data["per_task"][0]["metrics"]["successes"] = ["yes", False]
        elif failure == "duplicate_task":
            data["per_task"][1]["task_id"] = 0
        else:
            data["overall"]["eval_ep_s"] = -1
        path.write_text(json.dumps(data))
    result = cli("summarize_eval.py", tmp_path, "good")
    assert result.returncode == 1
    assert result.stderr and "== good:" not in result.stdout


def test_summary_accepts_converted_schema_without_timing_and_explicit_file(tmp_path):
    run = make_log(tmp_path)
    assert cli("ovla_to_json.py", tmp_path, "demo", "novideo").returncode == 0
    result = cli("summarize_eval.py", tmp_path, "--file", run / "dash/eval_info.json")
    assert result.returncode == 0, result.stderr
    assert "66.7%" in result.stdout and "n=3" in result.stdout


@pytest.mark.parametrize("script", ["ovla_to_json.py", "summarize_eval.py"])
@pytest.mark.parametrize("name", [".", "..", "../escape", "nested/run"])
def test_invalid_names_are_usage_errors_without_writes(tmp_path, script, name):
    result = cli(script, tmp_path, name)
    assert result.returncode == 2
    assert not list(tmp_path.iterdir())


def test_summary_requires_an_input(tmp_path):
    assert cli("summarize_eval.py", tmp_path).returncode == 2


def test_summary_accepts_existing_public_record_variants():
    records = list((ROOT / "dashboard/data").rglob("eval_info.json"))
    assert records
    for path in records:
        load_info(path)


@pytest.mark.parametrize("script", ["ovla_to_json.py", "summarize_eval.py"])
def test_run_lookup_requires_working_directory_configuration(tmp_path, script):
    result = cli(script, tmp_path, "demo", EMB_ROOT="")
    assert result.returncode == 2
    assert not list(tmp_path.iterdir())


def test_explicit_json_summary_needs_no_workstation_environment(tmp_path):
    path, _ = make_info(tmp_path)
    result = cli("summarize_eval.py", tmp_path, "--file", path, EMB_ROOT="")
    assert result.returncode == 0, result.stderr
    assert "75.0%" in result.stdout
