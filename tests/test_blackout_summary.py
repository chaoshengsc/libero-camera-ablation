"""Complete frozen runs summarize identically; missing evidence is not 0/100."""

import json
import shutil

import pytest
from test_analysis_tools import ROOT, cli, episode

DATA = ROOT / "dashboard/data"


@pytest.fixture
def blackout_inputs(tmp_path):
    root = tmp_path / "logs/eval"
    for name in ["smolvla2_spatial_500", "smol2_black_all", "pi0_spatial_500", "pi0_black_all", "pi05_spatial_500", "pi05_black_all"]:
        target = root / name / "out/eval_info.json"
        target.parent.mkdir(parents=True)
        shutil.copyfile(DATA / name / "eval_info.json", target)
    for name in ["openvla_spatial_500", "openvla_black_all"]:
        data = json.loads((DATA / name / "eval_info.json").read_text())
        target = root / name / "logs/eval.txt"
        target.parent.mkdir(parents=True)
        target.write_text("".join(episode(t["task"], f"fixture-{t['task_id']}-{i}.mp4", str(ok))
                                  for t in data["per_task"] for i, ok in enumerate(t["metrics"]["successes"])))
    return tmp_path


def test_complete_inputs_reproduce_published_blackout_summary(blackout_inputs):
    r = cli("summarize_blackout.py", blackout_inputs)
    assert r.returncode == 0, r.stderr
    output = blackout_inputs / "logs/eval/B_summary.json"
    assert json.loads(output.read_text()) == json.loads((DATA / "B_summary.json").read_text())
    before = output.read_bytes()
    assert cli("summarize_blackout.py", blackout_inputs).returncode != 0
    assert output.read_bytes() == before
    assert cli("summarize_blackout.py", blackout_inputs, "--output", output.with_name("new.json")).returncode == 0


@pytest.mark.parametrize("failure", ["missing", "empty", "truncated", "episode_count", "unknown_task", "exception", "ambiguous", "json_count"])
def test_bad_inputs_do_not_publish_summary(blackout_inputs, failure):
    root = blackout_inputs / "logs/eval"
    log = root / "openvla_black_all/logs/eval.txt"
    text = log.read_text()
    if failure == "missing":
        log.unlink()
    elif failure == "empty":
        log.write_text("")
    elif failure == "truncated":
        log.write_text(text + "Task: incomplete\n")
    elif failure == "episode_count":
        log.write_text(text + episode(json.loads((DATA / "openvla_spatial_500/eval_info.json").read_text())["per_task"][0]["task"], "extra.mp4", "False"))
    elif failure == "unknown_task":
        log.write_text(text.replace("pick up the black bowl", "unknown task", 1))
    elif failure == "exception":
        log.write_text(text + "Caught exception: simulator failed\n")
    elif failure == "ambiguous":
        log.with_name("another.txt").write_text(text)
    else:
        path = root / "pi0_black_all/out/eval_info.json"
        data = json.loads(path.read_text())
        data["per_task"][0]["metrics"]["successes"].pop()
        path.write_text(json.dumps(data))
    r = cli("summarize_blackout.py", blackout_inputs)
    assert r.returncode != 0
    assert not (root / "B_summary.json").exists()
