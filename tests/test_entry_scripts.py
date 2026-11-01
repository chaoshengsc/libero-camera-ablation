"""入口脚本的回归测试:用桩环境(假的 env.sh、lerobot-eval、lerobot 模块)实际执行 shell 与包装脚本。
覆盖整理仓库时出过或可能出的错:相对路径调用找不到脚本目录、缺参数时删掉整个结果目录、BLACKOUT 拼错被当成别的条件。"""
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def emb(tmp_path):
    """桩工作目录:env.sh 会切换目录(真实的 env.sh 也可能这样做),conda 是空函数,lerobot-eval 只把参数和环境变量写进文件。"""
    (tmp_path / "bin").mkdir()
    (tmp_path / "logs" / "eval" / "old_run").mkdir(parents=True)
    (tmp_path / "logs" / "train" / "old_run").mkdir(parents=True)
    (tmp_path / "env.sh").write_text('cd "$EMB_ROOT"\nconda() { :; }\nexport PATH="$EMB_ROOT/bin:$PATH"\n')
    stub = r'''#!/bin/bash
echo "$(basename "$0") $*" > "$EMB_ROOT/call.txt"
env | grep -E "^(BLACKOUT|TRAJ_OUT|WRAP|POLICY_SERVER)=" >> "$EMB_ROOT/call.txt"
echo "$*" >> "$EMB_ROOT/calls.log"
output=; previous=
for arg in "$@"; do
  case "$arg" in --output_dir=*) output=${arg#*=} ;; esac
  if [ "$previous" = --local_log_dir ]; then output=${arg%/logs}; fi
  previous=$arg
done
name=${output%/out}; name=${name##*/}
status=${STUB_EXIT:-0}
if [ -n "${STUB_FAIL_RUN:-}" ] && [ "$name" = "$STUB_FAIL_RUN" ]; then status=23; fi
if [ "$status" = 0 ] && [ -n "$output" ]; then
  mkdir -p "$output"
  if [[ "$*" = *train_statedrop.py* ]]; then
    if [ "${STUB_NO_CHECKPOINT:-0}" = 0 ]; then mkdir -p "$output/checkpoints/last/pretrained_model"; fi
    echo "[timing] avg 0.01s"
  fi
fi
exit "$status"
'''
    for name in ("lerobot-eval", "python"):
        p = tmp_path / "bin" / name
        p.write_text(stub)
        p.chmod(0o755)
    (tmp_path / "bin" / "nvidia-smi").write_text('#!/bin/bash\necho monitor >> "$EMB_ROOT/monitor_calls"\necho 256\n')
    (tmp_path / "bin" / "sleep").write_text('#!/bin/bash\n/bin/sleep 0.02\n')
    for name in ("nvidia-smi", "sleep"):
        (tmp_path / "bin" / name).chmod(0o755)
    (tmp_path / "cache" / "lerobot" / "lerobot" / "libero@fixture").mkdir(parents=True)
    return tmp_path


def run(cmd, emb, cwd=ROOT, **env):
    return subprocess.run(["bash", "-c", cmd], cwd=cwd, capture_output=True, text=True, timeout=15, env={**os.environ, "EMB_ROOT": str(emb), **env})


@pytest.mark.parametrize("cwd,src", [(ROOT, "scripts/common.sh"), (ROOT / "scripts" / "eval", "../common.sh"), (ROOT / "tests", str(ROOT / "scripts" / "common.sh"))])
def test_common_sh_finds_scripts_dir_from_any_cwd(emb, cwd, src):
    r = run(f"source {src}; echo $SCRIPTS", emb, cwd=cwd)
    assert r.stdout.strip() == str(ROOT / "scripts"), r.stderr


@pytest.mark.parametrize("script,kind", [("eval/run_libero.sh", "eval"), ("eval/run_ovla.sh", "eval"), ("train/run_train.sh", "train")])
def test_missing_args_do_not_delete_results(emb, script, kind):
    r = run(f"bash scripts/{script}", emb)
    assert r.returncode != 0 and "usage" in r.stderr
    assert (emb / "logs" / kind / "old_run").is_dir()


def test_run_libero_passes_arguments_and_wrapper(emb):
    r = run("bash scripts/eval/run_libero.sh demo 10 /ckpt/x 1 --policy.n_action_steps=5", emb)
    assert r.returncode == 0, r.stderr
    call = (emb / "call.txt").read_text()
    for flag in ("lerobot-eval", "--policy.path=/ckpt/x", "--env.task=libero_spatial", "--eval.batch_size=1", "--eval.n_episodes=10", "--seed=1000",
                 f"--output_dir={emb}/logs/eval/demo/out", "--policy.n_action_steps=5"):
        assert flag in call, flag
    assert "exit=0" in (emb / "logs" / "eval" / "demo" / "stdout.log").read_text()

    r = run("bash scripts/eval/run_libero.sh probe_demo 10 /ckpt/x 1", emb, WRAP="probe", BLACKOUT="freeze")
    call = (emb / "call.txt").read_text()
    assert f"python {ROOT}/scripts/eval/eval_probe.py" in call and "BLACKOUT=freeze" in call and f"TRAJ_OUT={emb}/logs/eval/probe_demo/traj.npz" in call

    assert run("bash scripts/eval/run_libero.sh invalid_demo 10 /ckpt/x 1", emb, WRAP="typo").returncode == 2
    assert not (emb / "logs/eval/invalid_demo").exists()


LEAF_RUNS = [
    ("eval/run_libero.sh", ["demo", "10", "/ckpt/x", "1"], "eval/demo"),
    ("eval/run_ovla.sh", ["demo", "10"], "eval/demo"),
    ("eval/run_act.sh", [], "eval/act_cube_500"),
    ("eval/run_dp_pusht.sh", [], "eval/dp_pusht_500"),
    ("train/run_train.sh", ["demo", "10", "1"], "train/demo"),
]


def run_entry(script, args, emb, **env):
    return run(shlex.join(["bash", str(ROOT / "scripts" / script), *args]), emb, **env)


@pytest.mark.parametrize("script,args,relative", LEAF_RUNS)
@pytest.mark.parametrize("existing", ["directory", "file", "symlink", "dangling_symlink"])
def test_existing_output_is_never_modified(emb, script, args, relative, existing):
    target = emb / "logs" / relative
    untouched = emb / "untouched"
    untouched.mkdir()
    sentinel = untouched / "keep.txt"
    sentinel.write_text("original")
    if existing == "directory":
        target.mkdir()
        (target / "keep.txt").write_text("original")
    elif existing == "file":
        target.write_text("original")
    else:
        target.symlink_to(untouched if existing == "symlink" else emb / "absent")
    r = run_entry(script, args, emb)
    assert r.returncode != 0
    assert sentinel.read_text() == "original"
    assert not (emb / "calls.log").exists()
    assert not (emb / "monitor_calls").exists()
    if existing == "directory":
        assert sorted(p.name for p in target.iterdir()) == ["keep.txt"]
        assert (target / "keep.txt").read_text() == "original"
    elif existing == "file":
        assert target.read_text() == "original"
    else:
        assert target.is_symlink()


@pytest.mark.parametrize("script,args,relative", LEAF_RUNS)
@pytest.mark.parametrize("status", [0, 23])
def test_leaf_propagates_child_status_and_logs_it(emb, script, args, relative, status):
    r = run_entry(script, args, emb, STUB_EXIT=str(status))
    assert r.returncode == status, r.stderr
    assert (emb / "logs" / relative / "stdout.log").read_text().splitlines().count(f"exit={status}") == 1
    assert (emb / "calls.log").is_file()


@pytest.mark.parametrize("script,args", [("eval/run_libero.sh", ["10", "/ckpt/x", "1"]),
                                         ("eval/run_ovla.sh", ["10"]), ("train/run_train.sh", ["10", "1"])])
@pytest.mark.parametrize("name", [".", "..", "../escape", "/absolute", "nested/run"])
def test_invalid_run_name_does_not_start_work(emb, script, args, name):
    r = run_entry(script, [name, *args], emb)
    assert r.returncode == 2
    assert not (emb / "calls.log").exists()
    assert not (emb / "monitor_calls").exists()


@pytest.mark.parametrize("script,args,first,later", [
    ("eval/run_pi0_full.sh", [], "pi0_smoke", "pi0_spatial_500"),
    ("eval/run_pi0_action_steps.sh", [], "pi0_nas10", "pi0_nas50"),
    ("eval/run_official_pi0.sh", ["single"], "ojx_drop_wrist", "ojx_drop_agent"),
    ("eval/run_official_pi0.sh", ["replay"], "ojx360_replay", "replay_open_loop.py"),
    ("train/run_statedrop_pipeline.sh", ["10"], "ft_p0", "ft_p05"),
    ("train/run_statedrop_pipeline.sh", ["10"], "eval_ft_p0_normal", "eval_ft_p0_black"),
])
def test_sequential_pipelines_stop_on_failure(emb, script, args, first, later):
    (emb / "tmp").mkdir()
    (emb / "tmp/openpi_authkey").write_text("fixture")
    r = run_entry(script, args, emb, STUB_FAIL_RUN=first)
    assert r.returncode == 23, r.stderr
    calls = (emb / "calls.log").read_text()
    assert first in calls and later not in calls
    done = emb / "logs/train/pipeline_done.flag"
    assert not done.exists() or done.read_text().strip() == "FAIL"


@pytest.mark.parametrize("script,fail_run,done", [
    ("eval/run_blackout_all.sh", "pi0_black_all", "blackout_done.flag"),
    ("eval/run_blackout_all.sh", "smol2_black_all", "blackout_done.flag"),
    ("eval/run_blackout_all.sh", "openvla_black_all", "blackout_done.flag"),
    ("eval/run_perturbation.sh", "pert_pi0_noise", None),
    ("eval/run_perturbation.sh", "pert_smol2_noise", None),
    ("eval/run_trajectory_and_single_camera.sh", "traj_pi0_normal", "trajectory_done.flag"),
    ("eval/run_trajectory_and_single_camera.sh", "traj_pi05_normal", "trajectory_done.flag"),
])
def test_parallel_pipelines_report_background_failure(emb, script, fail_run, done):
    r = run_entry(script, [], emb, STUB_FAIL_RUN=fail_run)
    assert r.returncode == 23, r.stderr
    if done:
        assert not (emb / "logs/eval" / done).exists()
    if script.endswith("run_blackout_all.sh") and fail_run != "openvla_black_all":
        assert "openvla_black_all" not in (emb / "calls.log").read_text()


@pytest.mark.parametrize("script,args,relative", LEAF_RUNS)
def test_failed_run_is_retained_and_cannot_be_reused(emb, script, args, relative):
    assert run_entry(script, args, emb, STUB_EXIT="23").returncode == 23
    output = emb / "logs" / relative
    before = {p.relative_to(output): p.read_bytes() for p in output.rglob('*') if p.is_file()}
    calls = (emb / "calls.log").read_bytes()
    assert run_entry(script, args, emb).returncode != 0
    assert {p.relative_to(output): p.read_bytes() for p in output.rglob('*') if p.is_file()} == before
    assert (emb / "calls.log").read_bytes() == calls


@pytest.mark.parametrize("script,args,relative", LEAF_RUNS)
def test_concurrent_starts_reserve_only_one_run(emb, script, args, relative):
    processes = [subprocess.Popen(["bash", str(ROOT / "scripts" / script), *args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  env={**os.environ, "EMB_ROOT": str(emb)}) for _ in range(2)]
    for p in processes:
        p.communicate(timeout=15)
    assert sorted(p.returncode for p in processes) == [0, 1]
    assert len((emb / "calls.log").read_text().splitlines()) == 1
    assert (emb / "logs" / relative / "stdout.log").read_text().splitlines().count("exit=0") == 1


PIPELINES = [
    ("eval/run_blackout_all.sh", [], 4, "eval/blackout_done.flag"),
    ("eval/run_perturbation.sh", [], 6, None),
    ("eval/run_trajectory_and_single_camera.sh", [], 10, "eval/trajectory_done.flag"),
    ("eval/run_pi0_full.sh", [], 2, None),
    ("eval/run_pi0_action_steps.sh", [], 2, None),
    ("eval/run_official_pi0.sh", ["single"], 2, None),
    ("train/run_statedrop_pipeline.sh", ["10"], 7, "train/pipeline_done.flag"),
]


@pytest.mark.parametrize("script,args,count,done", PIPELINES)
def test_successful_pipeline_completes_once(emb, script, args, count, done):
    (emb / "tmp").mkdir()
    (emb / "tmp/openpi_authkey").write_text("fixture")
    assert run_entry(script, args, emb).returncode == 0
    calls = (emb / "calls.log").read_bytes()
    assert len(calls.splitlines()) == count
    if done:
        assert (emb / "logs" / done).read_text().strip() == "DONE"
    assert run_entry(script, args, emb).returncode != 0
    assert (emb / "calls.log").read_bytes() == calls
    if done:
        assert (emb / "logs" / done).read_text().strip() == "DONE"


@pytest.mark.parametrize("script,args,existing", [
    ("eval/run_blackout_all.sh", [], "eval/blackout_done.flag"),
    ("eval/run_blackout_all.sh", [], "eval/openvla_black_all"),
    ("eval/run_perturbation.sh", [], "eval/pert_smol2_freeze"),
    ("eval/run_trajectory_and_single_camera.sh", [], "eval/trajectory_done.flag"),
    ("train/run_statedrop_pipeline.sh", ["10"], "train/pipeline.log"),
    ("train/run_statedrop_pipeline.sh", ["10"], "eval/eval_ft_p05_black"),
])
def test_pipeline_refuses_existing_outputs_before_launch(emb, script, args, existing):
    path = emb / "logs" / existing
    path.write_text("original")
    assert run_entry(script, args, emb).returncode != 0
    assert path.read_text() == "original"
    assert not (emb / "calls.log").exists()
    assert not (emb / "monitor_calls").exists()


def test_training_pipeline_preserves_intended_batch_fallback(emb):
    assert run_entry("train/run_statedrop_pipeline.sh", ["10"], emb, STUB_FAIL_RUN="probe_bs16").returncode == 0
    calls = (emb / "calls.log").read_text()
    assert "probe_bs8" in calls and "ft_p05" in calls and "eval_ft_p05_black" in calls
    assert (emb / "logs/train/pipeline_done.flag").read_text().strip() == "DONE"


def test_missing_checkpoint_is_not_reported_as_pipeline_success(emb):
    assert run_entry("train/run_statedrop_pipeline.sh", ["10"], emb, STUB_NO_CHECKPOINT="1").returncode == 1
    assert "eval_ft_" not in (emb / "calls.log").read_text()
    assert (emb / "logs/train/pipeline_done.flag").read_text().strip() == "FAIL"


def test_missing_openpi_auth_file_does_not_launch_evaluation(emb):
    assert run_entry("eval/run_official_pi0.sh", ["single"], emb).returncode != 0
    assert not (emb / "calls.log").exists()


@pytest.mark.parametrize("script,args,relative", LEAF_RUNS)
def test_output_root_with_spaces(emb, script, args, relative):
    spaced = emb / "work space"
    spaced.mkdir()
    for path in list(emb.iterdir()):
        if path != spaced:
            path.rename(spaced / path.name)
    assert run_entry(script, args, spaced).returncode == 0
    assert "exit=0" in (spaced / "logs" / relative / "stdout.log").read_text()


@pytest.mark.parametrize("script,args", [("eval/run_libero.sh", ["demo", "10", "/ckpt/x", "1"]),
                                         ("train/run_train.sh", ["demo", "10", "1"])])
@pytest.mark.parametrize("extra", [["--output_dir=elsewhere"], ["--output_dir", "elsewhere"]])
def test_extra_arguments_cannot_bypass_output_reservation(emb, script, args, extra):
    assert run_entry(script, [*args, *extra], emb).returncode == 2
    assert not (emb / "calls.log").exists()
    assert not (emb / "monitor_calls").exists()
    assert not (emb / "logs/eval/demo").exists()
    assert not (emb / "logs/train/demo").exists()


def test_act_preserves_legacy_log_and_uses_reserved_output(emb):
    old = emb / "logs/act_500.log"
    old.write_text("historical log")
    assert run_entry("eval/run_act.sh", [], emb).returncode == 0
    assert old.read_text() == "historical log"
    assert f"--output_dir={emb}/logs/eval/act_cube_500/out" in (emb / "call.txt").read_text()


def test_run_official_pi0_single_stage(emb):
    """官方 π0 单路阶段:两个条件都走 OpenPI 服务端(POLICY_SERVER)、256 渲染;未知阶段直接退出,不碰结果目录。"""
    (emb / "tmp").mkdir()
    (emb / "tmp" / "openpi_authkey").write_text("k")
    r = run("bash scripts/eval/run_official_pi0.sh single", emb)
    assert r.returncode == 0, r.stderr
    call = (emb / "call.txt").read_text()  # 桩每次覆盖,留下的是最后一个条件
    assert "BLACKOUT=drop_agent" in call and "POLICY_SERVER=18765" in call and "--env.observation_height=256" in call
    assert (emb / "logs" / "eval" / "ojx_drop_wrist").exists()
    r = run("bash scripts/eval/run_official_pi0.sh nope", emb)
    assert r.returncode == 2 and (emb / "logs" / "eval" / "old_run").exists()


def test_run_ovla_rejects_unknown_blackout(emb):
    r = run("bash scripts/eval/run_ovla.sh demo 10", emb, BLACKOUT="agent")
    assert r.returncode == 2 and not (emb / "logs" / "eval" / "demo").exists()


@pytest.fixture
def fake_lerobot(tmp_path):
    """假的 lerobot / torch / numpy 模块,只够让包装脚本走到取值校验和 main()。"""
    pkg = tmp_path / "stub" / "lerobot" / "scripts"
    pkg.mkdir(parents=True)
    (pkg.parent / "__init__.py").write_text("")
    (pkg / "__init__.py").write_text("")
    (pkg / "lerobot_eval.py").write_text("preprocess_observation = rollout = None\ndef main():\n    return 0\n")
    for sub, cls in (("pi0", "PI0Policy"), ("pi05", "PI05Policy")):  # eval_probe.py 在 π0/π0.5 的图像预处理外包一层
        d = pkg.parent / "policies" / sub
        d.mkdir(parents=True)
        for f in (d.parent / "__init__.py", d / "__init__.py"):
            f.write_text("")
        (d / f"modeling_{sub}.py").write_text(f"class {cls}:\n    _preprocess_images = select_action = None\n")
    proc = pkg.parent / "processor"  # eval_probe.py 修正 π0 增量动作还原时用的参考状态
    proc.mkdir()
    (proc / "__init__.py").write_text("")
    (proc / "relative_action_processor.py").write_text("class AbsoluteActionsProcessorStep:\n    __call__ = None\n"
                                                       "class RelativeActionsProcessorStep:\n    get_cached_state = None\n")
    for mod in ("torch", "numpy"):
        (tmp_path / "stub" / f"{mod}.py").write_text("")
    return str(tmp_path / "stub")


@pytest.mark.parametrize("script,good,bad", [("eval_blackout.py", ["all", "agent", "wrist"], ["none", "noise", "agnet"]),
                                             ("eval_probe.py", ["none", "all", "agent", "wrist", "noise", "freeze", "drop_wrist", "drop_agent", "drop_all",
                                                                "freeze_wrist", "freeze_agent"],
                                              ["agnet", "black", "drop", "drop_both"])])
def test_wrappers_validate_blackout(fake_lerobot, script, good, bad):
    def rc(mode):
        return subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "eval" / script)], capture_output=True,
                              env={"PYTHONPATH": fake_lerobot, "BLACKOUT": mode, "PATH": os.environ["PATH"]}).returncode
    assert all(rc(m) == 0 for m in good)
    assert all(rc(m) != 0 for m in bad)
