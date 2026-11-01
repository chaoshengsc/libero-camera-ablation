# 安装步骤

[English](INSTALL.md) · [项目首页](../README_CN.md) · [文档导航](README_CN.md)

原环境步骤按工作站实际执行记录整理（Ubuntu 24.04，RTX A5000，驱动570，无sudo、不用apt）；后续重建的补充步骤另行注明。
**没有在全新机器上从头重跑验证过**；版本号与 `constraints-*.txt` 一致。

**OpenPI/JAX原版π0服务端 + LeRobot客户端**另见[官方OpenPI安装与复现](OPENPI_CN.md)，其中补充独立环境、固定上游锁文件、原生权重、分词器缓存与验收步骤；下面三个环境不包含该服务端。

## 0. 工作目录与 Miniforge

```bash
git clone https://github.com/chaoshengsc/libero-camera-ablation.git && cd libero-camera-ablation
export REPO=$PWD                        # 本仓库的位置,后面的命令用它定位脚本
export EMB_ROOT=/path/to/workdir        # 大容量盘上的目录:环境、缓存、权重、日志都放这里
mkdir -p $EMB_ROOT/{home,tmp,cache,envs,src,ckpt,logs/pip}
cp env/env.sh.example $EMB_ROOT/env.sh
cp env/condarc.example $EMB_ROOT/home/.condarc   # 把里面的 ${EMB_ROOT} 换成实际路径
cp env/constraints-*.txt $EMB_ROOT/logs/pip/
```

`env.sh` 把 HOME、缓存、临时目录都重定向到 `$EMB_ROOT`。需要和同机其他项目隔离时加 `export EMB_STRICT=1`：它会要求 `$EMB_ROOT` 是独立挂载点且权限为 700，否则拒绝加载。
Miniforge（本项目用 26.7.2）装到 `$EMB_ROOT/miniforge3`，不做 `conda init`。之后每个终端先 `source $EMB_ROOT/env.sh`。

源码固定到这些版本，克隆到 `$EMB_ROOT/src/`：

| 仓库 | 版本 |
|---|---|
| huggingface/lerobot | v0.6.1(7e241bd6) |
| openvla/openvla | c8f03f48 |
| Lifelong-Robot-Learning/LIBERO | 8f1084e3 |

```bash
cd $EMB_ROOT/src
git clone https://github.com/huggingface/lerobot.git && git -C lerobot checkout 7e241bd6
git clone https://github.com/openvla/openvla.git && git -C openvla checkout c8f03f48
git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git && git -C LIBERO checkout 8f1084e3
```

## 1. `lerobot` 环境（ACT、Diffusion Policy）

```bash
conda create -y -n lerobot python=3.12 git curl tmux cmake "ffmpeg=7.1.1"
conda activate lerobot && cd $EMB_ROOT/src/lerobot
C=$EMB_ROOT/logs/pip/constraints-torch.txt
pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu128 "torch==2.11.0+cu128" "torchvision==0.26.0+cu128"
pip install --only-binary=:all: -c $C -e ".[aloha]"
# Diffusion Policy · PushT：gym-pusht 不带依赖装，避免把 opencv-python-headless 换掉
pip install --only-binary=:all: -c $C --no-deps "gym-pusht==0.1.6"
pip install --only-binary=:all: -c $C "pymunk>=6.6.0,<7.0.0" "pygame>=2.5.2" "scikit-image>=0.22.0" "shapely>=2.0.3"
pip install --only-binary=:all: -c $C "diffusers>=0.38.0,<0.40.0"
```

- torch 必须从 cu128 索引装：PyPI 默认的 torch 是 CUDA 13 版，驱动 570 不支持。
- ffmpeg 固定 7.1.1：torchcodec 0.11 不支持 ffmpeg 9。

自检：`python $REPO/scripts/checks/torch_check.py`，同目录下还有 `egl_smoke.py`、`codec_check.py`。

## 2. `openvla` 环境

```bash
conda create -y -n openvla python=3.10.13 git ninja
conda activate openvla
C=$EMB_ROOT/logs/pip/constraints-ovla.txt
pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu121 torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0
(cd $EMB_ROOT/src/openvla && pip install -c $C -e .)
# flash-attn：直接装官方预编译 wheel（源码编译要求 CUDA_HOME）
pip install -c $C "https://github.com/Dao-AILab/flash-attention/releases/download/v2.5.5/flash_attn-2.5.5+cu122torch2.2cxx11abiFALSE-cp310-cp310-linux_x86_64.whl"
(cd $EMB_ROOT/src/LIBERO && pip install --no-deps -e . --config-settings editable_mode=compat)
pip install -c $C -r $EMB_ROOT/src/openvla/experiments/robot/libero/libero_requirements.txt
pip install --only-binary=:all: -c $C "mujoco==3.3.2" "tensorflow-metadata==1.17.1" "protobuf==4.21.12"
```

- MuJoCo ≥ 3.3.3 会让 LIBERO 渲染变暗（LIBERO issue #88），固定 3.3.2。
- LIBERO 必须用 `editable_mode=compat`，否则装完 import 不到。

## 3. `smolvla` 环境（SmolVLA、π0、π0.5，评测与训练共用）

```bash
conda create -y -n smolvla python=3.12 git cmake "ffmpeg=7.1.1"
conda activate smolvla && cd $EMB_ROOT/src/lerobot
pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu128 "torch==2.11.0+cu128" "torchvision==0.26.0+cu128"
CMAKE_POLICY_VERSION_MINIMUM=3.5 pip install --prefer-binary -c $EMB_ROOT/logs/pip/constraints-smolvla.txt -e ".[smolvla,libero]"
```

- `CMAKE_POLICY_VERSION_MINIMUM=3.5` 是为了让 `egl_probe` 在新版 CMake 下能编译。
- 不能和 `lerobot` 环境合并：这里 mujoco 要 3.3.2，而 ACT 用的 dm_control 要求 ≥ 3.8.1。

## 4. 权重

用 `hf download <仓库> --revision <commit> --local-dir $EMB_ROOT/ckpt/<目录名>` 下载，目录名见 `scripts/common.sh`（格式 `仓库名@commit 前 8 位`）；`results/reproduction.csv`也使用短revision。后续底座准备使用完整revision。例如：

```bash
hf download lerobot/pi05_libero_finetuned_v044 --revision 8e174154 --local-dir $EMB_ROOT/ckpt/pi05_libero_finetuned_v044@8e174154
```

- **ACT、Diffusion Policy** 的权重是旧格式，先迁移（DP 需经 `migrate_tuplefix.py` 包一层，修 list/tuple 解码问题）：
  ```bash
  conda activate lerobot
  # ACT：用 LeRobot 自带的迁移脚本
  CK=$EMB_ROOT/ckpt/act_aloha_sim_transfer_cube_human@ba73b276
  python $EMB_ROOT/src/lerobot/src/lerobot/processor/migrate_policy_normalization.py --pretrained-path $CK --output-dir ${CK}_migrated
  # Diffusion Policy：只用这一条（包装脚本内部会调用上面的迁移脚本）
  CK=$EMB_ROOT/ckpt/diffusion_pusht@84a7c231
  python $REPO/scripts/eval/migrate_tuplefix.py --pretrained-path $CK --output-dir ${CK}_migrated
  ```
- **LeRobot π0、π0.5** 的分词器来自受限仓库 `google/paligemma-3b-pt-224`：需自己在 Hugging Face 上申请授权后下载分词器文件，
  再把权重目录里 `policy_preprocessor.json` 的 `tokenizer_name` 改成本地路径。本仓库不提供该分词器。
- **OpenPI原版π0**使用原生Orbax检查点及独立GCS分词器缓存，按[OpenPI指南](OPENPI_CN.md#3-原生权重归一化与分词器)准备，不套用上面的LeRobot权重/分词器步骤。
- **状态置零微调的训练数据**：`lerobot/libero` 数据集（约 1.9 GB），放在 `$EMB_ROOT/cache/lerobot/lerobot/libero@<commit>`。

### 4.1 离线评测前准备

`run_libero.sh`会设置`HF_HUB_OFFLINE=1`。先按所选模型准备本地策略及依赖，LIBERO素材也须就绪；下载SmolVLA策略权重不等于底座已缓存。**下方底座下载块仅用于SmolVLA，P1和OpenPI原版不需要它。** 这里的补充步骤按既有版本和源码整理，**本次未执行下载、模型加载或新机器验收**。

SmolVLA复现使用的底座为`HuggingFaceTB/SmolVLM2-500M-Video-Instruct@7b375e1b73b11138ff12fe22c8f2822d8fe03467`。公开策略配置的`load_vlm_weights=True`，初始化仍会读取底座权重和processor；只准备配置文件不够。[策略配置](https://huggingface.co/lerobot/smolvla_libero/blob/31d453f7/config.json)及[固定底座文件](https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct/tree/7b375e1b73b11138ff12fe22c8f2822d8fe03467)可核对来源。

**以下会下载和写缓存。** 在Linux工作站任意目录、完成前述环境安装后执行；`EMB_ROOT`已设置。保留`HF_HUB_CACHE`设置供后续评测使用。只取所需权重与配置，不下载ONNX变体：

```bash
source "$EMB_ROOT/env.sh"
conda activate smolvla
export HF_HUB_CACHE="$HF_HOME/hub"
(
  set -e
  export BASE_REPO=HuggingFaceTB/SmolVLM2-500M-Video-Instruct
  export BASE_REV=7b375e1b73b11138ff12fe22c8f2822d8fe03467
  hf download "$BASE_REPO" --revision "$BASE_REV" \
    --include '*.json' '*.txt' '*.model' model.safetensors
  python - <<'PY'
import os
from pathlib import Path

from huggingface_hub import hf_hub_download

repo_id, revision = os.environ["BASE_REPO"], os.environ["BASE_REV"]
cache = Path(os.environ["HF_HUB_CACHE"])
model = cache / ("models--" + repo_id.replace("/", "--"))
snapshot = model / "snapshots" / revision
required = ("config.json", "model.safetensors", "tokenizer.json",
            "tokenizer_config.json", "preprocessor_config.json", "processor_config.json")
if not all((snapshot / name).is_file() for name in required):
    raise SystemExit("Incomplete pinned base-model snapshot; stop")
ref = model / "refs/main"
if ref.exists() or ref.is_symlink():
    if ref.read_text().strip() != revision:
        raise SystemExit("Existing main cache reference differs; do not overwrite it")
else:
    ref.parent.mkdir(parents=True, exist_ok=True)
    with ref.open("x") as output:
        output.write(revision)
for name in required:
    path = hf_hub_download(repo_id, name, revision="main",
                           cache_dir=str(cache), local_files_only=True)
    if Path(path).parent.name != revision:
        raise SystemExit("Offline lookup resolved to a different revision")
print("Pinned base-model files resolve offline; no model loaded")
PY
)
```

按commit下载不会自动建立`refs/main`，而该版LeRobot以仓库名读取底座，未传revision；此步骤将**本项目缓存的main别名**固定到已下载commit，不修改远端分支。已有别名不一致会停止，不删除或覆盖旧缓存。需要时核查原来源后另准备隔离缓存，不能直接改指针强行通过。

末尾预期为`Pinned base-model files resolve offline; no model loaded`。这是本地文件存在和离线解析检查，不是权重内容哈希校验、模型推理或成功率验收。每个新评测终端加载`env.sh`后同样设置`HF_HUB_CACHE="$HF_HOME/hub"`；缺文件应补齐固定版本，不通过解除离线模式混入新版本。

LeRobot π0/π0.5仍按上一节配置本地分词器；OpenPI原版按独立指南准备GCS缓存。LIBERO的BDDL、初始状态与assets目录也须在本地，并与固定的`hf-libero`/LIBERO源码配置一致。**单纯评测无需下载`lerobot/libero`训练数据。** 完成这些准备后，再选择[最小相机入口](../scripts/README_CN.md#最小相机评测)或[P1启动步骤](../scripts/README_CN.md#p1启动步骤仅供获准的独立重复)。

## 5. 跑评测

```bash
bash "$REPO/scripts/eval/run_act.sh"  # ACT,500回合约17分钟
CK="$EMB_ROOT/ckpt/pi05_libero_finetuned_v044@8e174154"
RUN=pi05_spatial_check
bash "$REPO/scripts/eval/run_libero.sh" "$RUN" 50 "$CK" 1 \
  --policy.n_action_steps=10
python3 "$REPO/scripts/analysis/summarize_eval.py" "$RUN"
```

输出在 `$EMB_ROOT/logs/eval/<run_name>/`；`stdout.log` 最后一行 `exit=0` 表示正常结束。各实验的入口见 `scripts/README_CN.md`。

`CK`须指向已准备的权重，`RUN`须未被使用；该LIBERO命令每任务50回合、共500回合。只需十回合相机检查时，使用[最小示例](../scripts/README_CN.md#最小相机评测)。

结果注册、专题所需配对/哈希记录及完整重建顺序统一见[脚本索引](../scripts/README_CN.md#已有数据的分析与出图)；只复制JSON不会自动把新运行注册到看板。

## 6. 官方OpenPI π0

接着阅读[独立指南](OPENPI_CN.md)：已有版本 → JAX独立环境 → 原生权重/缓存 → 纯配置客户端 → 本机服务端/客户端 → 分阶段验收。命令整理自历史管线与重建的安装步骤，本次文档更新未重新安装依赖或运行新实验；恢复实验和P3继续暂停。

## 7. 验证范围

2026-11-01在**既有**Ubuntu/RTX A5000客户端环境做了有界入口检查，复用已装包、权重及素材缓存；未执行安装或权重/分词器下载。

| 入口 | 实际检查 | 范围 |
|---|---|---|
| 最小相机全黑示例 | 10回合、实际退出0、两路黑图、有限轨迹，十个首帧哈希均与旧实验匹配 | 工程验收，不并入正式结果表 |
| P2打包后的`--self-only` | 自回放10/10、动作前缀精确一致、十个原始状态匹配、正式回合0 | 自检门槛与产物验收，不新增400目标结果 |
| 无效输入/已有输出 | 返回非零，旧失败/成功工件均未改变 | 真实错误传播与覆盖保护 |

已装`hf-libero` 0.1.4的BDDL/初始状态文件随包提供；本机另行缓存的网格/纹理经`Path.home() / ".cache/libero/assets"`解析，加载`env.sh`后对应`$EMB_ROOT/home/.cache/libero/assets`。运行前已核对`articulated_objects`、`stable_scanned_objects`、`turbosquid_objects`、`stable_hope_objects`及`scenes`五个目录均在，没有触发素材下载；只设置`HF_HOME`不等于准备了这份独立目录。

这不构成干净机器安装验收。没有重跑完整P1、P2正式阶段或原生OpenPI服务；历史正式结果与区间保持不变。检查及一次已修正的stdout解析失败保留在[实验日志](NOTES_CN.md#有界入口验收与v15快照2026-11-01)。恢复实验和P3继续暂停。
