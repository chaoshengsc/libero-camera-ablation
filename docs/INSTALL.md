# 安装步骤

按当时在工作站上实际执行的步骤整理(Ubuntu 24.04,RTX A5000,驱动 570,无 sudo、不用 apt)。
**没有在全新机器上从头重跑验证过**;版本号与 `constraints-*.txt` 一致。

## 0. 工作目录与 Miniforge

```bash
export EMB_ROOT=/path/to/workdir        # 大容量盘上的目录,权限 700
mkdir -p $EMB_ROOT/{home,tmp,cache,envs,src,ckpt,logs/pip}
cp env/env.sh.example $EMB_ROOT/env.sh
cp env/condarc.example $EMB_ROOT/home/.condarc   # 把里面的 ${EMB_ROOT} 换成实际路径
cp env/constraints-*.txt $EMB_ROOT/logs/pip/
```

`env.sh` 默认要求 `$EMB_ROOT` 是一个独立挂载点且权限为 700(为了和同机其他项目隔离);不需要这层隔离时删掉开头那段检查即可。
Miniforge(本项目用 26.7.2)装到 `$EMB_ROOT/miniforge3`,不做 `conda init`。之后每个终端先 `source $EMB_ROOT/env.sh`。

源码固定到这些版本,克隆到 `$EMB_ROOT/src/`:

| 仓库 | 版本 |
|---|---|
| huggingface/lerobot | v0.6.1(7e241bd6) |
| openvla/openvla | c8f03f48 |
| Lifelong-Robot-Learning/LIBERO | 8f1084e3 |

## 1. `lerobot` 环境(ACT、Diffusion Policy)

```bash
conda create -y -n lerobot python=3.12 git curl tmux cmake "ffmpeg=7.1.1"
conda activate lerobot && cd $EMB_ROOT/src/lerobot
C=$EMB_ROOT/logs/pip/constraints-torch.txt
pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu128 "torch==2.11.0+cu128" "torchvision==0.26.0+cu128"
pip install --only-binary=:all: -c $C -e ".[aloha]"
# Diffusion Policy · PushT:gym-pusht 不带依赖装,避免把 opencv-python-headless 换掉
pip install --only-binary=:all: -c $C --no-deps "gym-pusht==0.1.6"
pip install --only-binary=:all: -c $C "pymunk>=6.6.0,<7.0.0" "pygame>=2.5.2" "scikit-image>=0.22.0" "shapely>=2.0.3"
pip install --only-binary=:all: -c $C "diffusers>=0.38.0,<0.40.0"
```

- torch 必须从 cu128 索引装:PyPI 默认的 torch 是 CUDA 13 版,驱动 570 不支持。
- ffmpeg 固定 7.1.1:torchcodec 0.11 不支持 ffmpeg 9。

自检:`python scripts/checks/torch_check.py`、`egl_smoke.py`、`codec_check.py`。

## 2. `openvla` 环境

```bash
conda create -y -n openvla python=3.10.13 git ninja
conda activate openvla
C=$EMB_ROOT/logs/pip/constraints-ovla.txt
pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu121 torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0
(cd $EMB_ROOT/src/openvla && pip install -c $C -e .)
# flash-attn:直接装官方预编译 wheel(源码编译要求 CUDA_HOME)
pip install -c $C "https://github.com/Dao-AILab/flash-attention/releases/download/v2.5.5/flash_attn-2.5.5+cu122torch2.2cxx11abiFALSE-cp310-cp310-linux_x86_64.whl"
(cd $EMB_ROOT/src/LIBERO && pip install --no-deps -e . --config-settings editable_mode=compat)
pip install -c $C -r $EMB_ROOT/src/openvla/experiments/robot/libero/libero_requirements.txt
pip install --only-binary=:all: -c $C "mujoco==3.3.2" "tensorflow-metadata==1.17.1" "protobuf==4.21.12"
```

- MuJoCo ≥ 3.3.3 会让 LIBERO 渲染变暗(LIBERO issue #88),固定 3.3.2。
- LIBERO 必须用 `editable_mode=compat`,否则装完 import 不到。

## 3. `smolvla` 环境(SmolVLA、π0、π0.5,评测与训练共用)

```bash
conda create -y -n smolvla python=3.12 git cmake "ffmpeg=7.1.1"
conda activate smolvla && cd $EMB_ROOT/src/lerobot
pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu128 "torch==2.11.0+cu128" "torchvision==0.26.0+cu128"
CMAKE_POLICY_VERSION_MINIMUM=3.5 pip install --prefer-binary -c $EMB_ROOT/logs/pip/constraints-smolvla.txt -e ".[smolvla,libero]"
```

- `CMAKE_POLICY_VERSION_MINIMUM=3.5` 是为了让 `egl_probe` 在新版 CMake 下能编译。
- 不能和 `lerobot` 环境合并:这里 mujoco 要 3.3.2,而 ACT 用的 dm_control 要求 ≥ 3.8.1。

## 4. 权重

用 `hf download <仓库> --revision <commit> --local-dir $EMB_ROOT/ckpt/<目录名>` 下载,目录名见 `scripts/common.sh`(格式 `仓库名@commit 前 8 位`)。

- **ACT、Diffusion Policy** 的权重是旧格式,先迁移(DP 需经 `migrate_tuplefix.py` 包一层,修 list/tuple 解码问题):
  ```bash
  python $EMB_ROOT/src/lerobot/src/lerobot/processor/migrate_policy_normalization.py --pretrained-path $C --output-dir ${C}_migrated
  python scripts/eval/migrate_tuplefix.py --pretrained-path $C --output-dir ${C}_migrated   # DP
  ```
- **π0、π0.5** 的分词器来自受限仓库 `google/paligemma-3b-pt-224`:需自己在 Hugging Face 上申请授权后下载分词器文件,
  再把权重目录里 `policy_preprocessor.json` 的 `tokenizer_name` 改成本地路径。本仓库不提供该分词器。
- **方向 3 的训练数据**:`lerobot/libero` 数据集(约 1.9 GB),放在 `$EMB_ROOT/cache/lerobot/lerobot/libero@<commit>`。

## 5. 跑评测

```bash
bash scripts/eval/run_act.sh                                   # ACT,500 回合约 17 分钟
bash scripts/eval/run_libero.sh pi05_spatial_500 50 <权重目录> 1 --policy.n_action_steps=10
python3 scripts/analysis/summarize_eval.py pi05_spatial_500            # 成功率与 95% 置信区间
```

输出在 `$EMB_ROOT/logs/eval/<run_name>/`;`stdout.log` 最后一行 `exit=0` 表示正常结束。各实验的入口见 `scripts/README.md`。
