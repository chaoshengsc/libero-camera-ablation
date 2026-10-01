"""入口脚本的回归测试:用桩环境(假的 env.sh、lerobot-eval、lerobot 模块)实际执行 shell 与包装脚本。
覆盖整理仓库时出过或可能出的错:相对路径调用找不到脚本目录、缺参数时删掉整个结果目录、BLACKOUT 拼错被当成别的条件。"""
import os
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
    stub = "#!/bin/bash\necho \"$(basename $0) $*\" > $EMB_ROOT/call.txt\nenv | grep -E \"^(BLACKOUT|TRAJ_OUT|WRAP)=\" >> $EMB_ROOT/call.txt\nexit 0\n"
    for name in ("lerobot-eval", "python"):
        p = tmp_path / "bin" / name
        p.write_text(stub)
        p.chmod(0o755)
    return tmp_path


def run(cmd, emb, cwd=ROOT, **env):
    return subprocess.run(["bash", "-c", cmd], cwd=cwd, capture_output=True, text=True, env={**os.environ, "EMB_ROOT": str(emb), **env})


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

    r = run("bash scripts/eval/run_libero.sh demo 10 /ckpt/x 1", emb, WRAP="probe", BLACKOUT="freeze")
    call = (emb / "call.txt").read_text()
    assert f"python {ROOT}/scripts/eval/eval_probe.py" in call and "BLACKOUT=freeze" in call and f"TRAJ_OUT={emb}/logs/eval/demo/traj.npz" in call

    assert run("bash scripts/eval/run_libero.sh demo 10 /ckpt/x 1", emb, WRAP="typo").returncode == 2


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
    for mod in ("torch", "numpy"):
        (tmp_path / "stub" / f"{mod}.py").write_text("")
    return str(tmp_path / "stub")


@pytest.mark.parametrize("script,good,bad", [("eval_blackout.py", ["all", "agent", "wrist"], ["none", "noise", "agnet"]),
                                             ("eval_probe.py", ["none", "all", "agent", "wrist", "noise", "freeze"], ["agnet", "black"])])
def test_wrappers_validate_blackout(fake_lerobot, script, good, bad):
    def rc(mode):
        return subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "eval" / script)], capture_output=True,
                              env={"PYTHONPATH": fake_lerobot, "BLACKOUT": mode, "PATH": os.environ["PATH"]}).returncode
    assert all(rc(m) == 0 for m in good)
    assert all(rc(m) != 0 for m in bad)
