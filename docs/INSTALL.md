# Installation

English | [中文](INSTALL_CN.md)

These are the steps that were actually run on the workstation (Ubuntu 24.04, RTX A5000, driver 570, no sudo, no apt).
**They have not been re-run from scratch on a clean machine.** Version numbers match `constraints-*.txt`.

## 0. Working directory and Miniforge

```bash
git clone https://github.com/chaoshengsc/libero-camera-ablation.git && cd libero-camera-ablation
export REPO=$PWD                        # location of this repo; later commands use it to find scripts
export EMB_ROOT=/path/to/workdir        # a directory on a large disk: environments, caches, checkpoints and logs all go here
mkdir -p $EMB_ROOT/{home,tmp,cache,envs,src,ckpt,logs/pip}
cp env/env.sh.example $EMB_ROOT/env.sh
cp env/condarc.example $EMB_ROOT/home/.condarc   # replace ${EMB_ROOT} inside with the actual path
cp env/constraints-*.txt $EMB_ROOT/logs/pip/
```

`env.sh` redirects HOME, caches and temporary directories to `$EMB_ROOT`. To isolate this project from others on the same machine, add `export EMB_STRICT=1`: `env.sh` then refuses to load unless `$EMB_ROOT` is its own mount point with mode 700.
Install Miniforge (this project used 26.7.2) to `$EMB_ROOT/miniforge3` without running `conda init`. After that, run `source $EMB_ROOT/env.sh` first in every terminal.

Clone the sources into `$EMB_ROOT/src/` at these pinned versions:

| Repository | Version |
|---|---|
| huggingface/lerobot | v0.6.1 (7e241bd6) |
| openvla/openvla | c8f03f48 |
| Lifelong-Robot-Learning/LIBERO | 8f1084e3 |

```bash
cd $EMB_ROOT/src
git clone https://github.com/huggingface/lerobot.git && git -C lerobot checkout 7e241bd6
git clone https://github.com/openvla/openvla.git && git -C openvla checkout c8f03f48
git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git && git -C LIBERO checkout 8f1084e3
```

## 1. `lerobot` environment (ACT, Diffusion Policy)

```bash
conda create -y -n lerobot python=3.12 git curl tmux cmake "ffmpeg=7.1.1"
conda activate lerobot && cd $EMB_ROOT/src/lerobot
C=$EMB_ROOT/logs/pip/constraints-torch.txt
pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu128 "torch==2.11.0+cu128" "torchvision==0.26.0+cu128"
pip install --only-binary=:all: -c $C -e ".[aloha]"
# Diffusion Policy on PushT: install gym-pusht without dependencies so it does not replace opencv-python-headless
pip install --only-binary=:all: -c $C --no-deps "gym-pusht==0.1.6"
pip install --only-binary=:all: -c $C "pymunk>=6.6.0,<7.0.0" "pygame>=2.5.2" "scikit-image>=0.22.0" "shapely>=2.0.3"
pip install --only-binary=:all: -c $C "diffusers>=0.38.0,<0.40.0"
```

- torch has to come from the cu128 index: the default torch on PyPI is built for CUDA 13, which driver 570 does not support.
- ffmpeg is pinned to 7.1.1: torchcodec 0.11 does not support ffmpeg 9.

Sanity check: `python $REPO/scripts/checks/torch_check.py`. The same directory also has `egl_smoke.py` and `codec_check.py`.

## 2. `openvla` environment

```bash
conda create -y -n openvla python=3.10.13 git ninja
conda activate openvla
C=$EMB_ROOT/logs/pip/constraints-ovla.txt
pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu121 torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0
(cd $EMB_ROOT/src/openvla && pip install -c $C -e .)
# flash-attn: install the official prebuilt wheel (building from source requires CUDA_HOME)
pip install -c $C "https://github.com/Dao-AILab/flash-attention/releases/download/v2.5.5/flash_attn-2.5.5+cu122torch2.2cxx11abiFALSE-cp310-cp310-linux_x86_64.whl"
(cd $EMB_ROOT/src/LIBERO && pip install --no-deps -e . --config-settings editable_mode=compat)
pip install -c $C -r $EMB_ROOT/src/openvla/experiments/robot/libero/libero_requirements.txt
pip install --only-binary=:all: -c $C "mujoco==3.3.2" "tensorflow-metadata==1.17.1" "protobuf==4.21.12"
```

- MuJoCo ≥ 3.3.3 makes LIBERO render darker (LIBERO issue #88), so it is pinned to 3.3.2.
- LIBERO must be installed with `editable_mode=compat`; otherwise it cannot be imported after installation.

## 3. `smolvla` environment (SmolVLA, π0, π0.5; shared by evaluation and training)

```bash
conda create -y -n smolvla python=3.12 git cmake "ffmpeg=7.1.1"
conda activate smolvla && cd $EMB_ROOT/src/lerobot
pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu128 "torch==2.11.0+cu128" "torchvision==0.26.0+cu128"
CMAKE_POLICY_VERSION_MINIMUM=3.5 pip install --prefer-binary -c $EMB_ROOT/logs/pip/constraints-smolvla.txt -e ".[smolvla,libero]"
```

- `CMAKE_POLICY_VERSION_MINIMUM=3.5` lets `egl_probe` compile with recent CMake.
- This environment cannot be merged with `lerobot`: it needs mujoco 3.3.2, while the dm_control used by ACT requires ≥ 3.8.1.

## 4. Checkpoints

Download with `hf download <repo> --revision <commit> --local-dir $EMB_ROOT/ckpt/<dir>`. Directory names are listed in `scripts/common.sh` (format: `repo name@first 8 characters of the commit`); full commits are in `results/reproduction.csv`. For example:

```bash
hf download lerobot/pi05_libero_finetuned_v044 --revision 8e174154 --local-dir $EMB_ROOT/ckpt/pi05_libero_finetuned_v044@8e174154
```

- **ACT and Diffusion Policy** checkpoints are in the old format and have to be migrated first (DP goes through `migrate_tuplefix.py`, a wrapper that fixes a list/tuple decoding problem):
  ```bash
  conda activate lerobot
  # ACT: use the migration script that ships with LeRobot
  CK=$EMB_ROOT/ckpt/act_aloha_sim_transfer_cube_human@ba73b276
  python $EMB_ROOT/src/lerobot/src/lerobot/processor/migrate_policy_normalization.py --pretrained-path $CK --output-dir ${CK}_migrated
  # Diffusion Policy: run only this one (the wrapper calls the migration script above internally)
  CK=$EMB_ROOT/ckpt/diffusion_pusht@84a7c231
  python $REPO/scripts/eval/migrate_tuplefix.py --pretrained-path $CK --output-dir ${CK}_migrated
  ```
- **π0 and π0.5** use the tokenizer from the gated repository `google/paligemma-3b-pt-224`: request access on Hugging Face yourself, download the tokenizer files,
  then set `tokenizer_name` in the checkpoint's `policy_preprocessor.json` to the local path. This repo does not distribute the tokenizer.
- **Training data for the state-zeroing fine-tune**: the `lerobot/libero` dataset (about 1.9 GB), placed at `$EMB_ROOT/cache/lerobot/lerobot/libero@<commit>`.

## 5. Running evaluations

```bash
bash $REPO/scripts/eval/run_act.sh                             # ACT, 500 episodes, about 17 minutes
bash $REPO/scripts/eval/run_libero.sh pi05_spatial_500 50 <checkpoint dir> 1 --policy.n_action_steps=10
python3 $REPO/scripts/analysis/summarize_eval.py pi05_spatial_500      # success rate and 95% confidence interval
```

Outputs go to `$EMB_ROOT/logs/eval/<run_name>/`; a last line of `exit=0` in `stdout.log` means the run finished normally. Entry points for each experiment are listed in `scripts/README.md`.

To bring a new result into the dashboard and figures, copy its `eval_info.json` to `dashboard/data/<run_name>/`, then run `python3 dashboard/build.py && python3 scripts/analysis/make_figures.py`.
