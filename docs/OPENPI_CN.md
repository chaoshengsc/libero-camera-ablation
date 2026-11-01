# 官方 OpenPI π0：安装与复现

[English](OPENPI.md) · [安装指南](INSTALL_CN.md) · [脚本索引](../scripts/README_CN.md) · [完整结果](EXPERIMENTS_CN.md#15-官方-π0-对照)

本文按2026-10-28至29日的记录整理 **OpenPI/JAX原版服务端 + LeRobot LIBERO客户端**。这是通过验收的路径：冒烟 **50/50**，随后正常条件 **482/500 = 96.4%**。另行试用的HF检查点冒烟 **0/50**，其同源性核验未通过，不能视为原生权重的验证转换；保留为失败诊断，不是安装前提（[证据](../dashboard/data/protocol_audit/checkpoint_identity.json)）。

这里复现本仓库的历史客户端协议：Spatial为**280控制步＋10步稳定等待**；固定版本的[OpenPI上游示例](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/examples/libero/main.py)为220＋10步。96.4%是本协议下的官方权重评测结果，不是与上游96.8%完全同协议的复现；对照范围见[协议与验收表](EXPERIMENTS_CN.md#3-评测协议与验收范围)。

以下命令用于说明配置和执行方法，**编写本文时没有重新执行安装或实验**。2026-11-01只读核对了已装包元数据、部分源码指纹、客户端配置及历史日志；尚未在干净机器上从头安装，也未新增模型或仿真运行。恢复实验和P3继续暂停。

## 1. 已有运行配置

| 部分 | 记录值 |
|---|---|
| 工作站 | Ubuntu 24.04、RTX A5000 24 GB、驱动570；无sudo、不用apt |
| OpenPI源码 | [`215abfb217dbac7d5f1273282331b9b1866c0479`](https://github.com/Physical-Intelligence/openpi/tree/215abfb217dbac7d5f1273282331b9b1866c0479) |
| 服务端环境 | Python 3.11.18；uv 0.9.5；`uv sync --frozen` |
| 已装JAX包 | jax / jaxlib / jax-cuda12-plugin / jax-cuda12-pjrt均为0.5.3 |
| 服务端其他已装包 | flax 0.10.2；orbax-checkpoint 0.11.13；NumPy 1.26.4；tensorstore 0.1.74；ml-dtypes 0.4.1 |
| 客户端环境 | `smolvla`：LeRobot v0.6.1（`7e241bd6`）、torch 2.11.0+cu128、MuJoCo 3.3.2、robosuite 1.4.0、hf-libero 0.1.4 |
| 原生检查点 | `gs://openpi-assets/checkpoints/pi0_libero`；历史下载19个文件，共12,014,131,888字节 |
| 评测设置 | LIBERO-Spatial十任务、batch1、seed1000、280控制步＋10步稳定等待、每次查询后执行5步动作 |
| 图像 | 原主实验以256渲染，再缩放为224模型输入；另有360渲染复测 |

服务端与客户端使用**不同环境**。OpenPI锁文件自带Git固定版本的LeRobot依赖，不是负责仿真的v0.6.1客户端。10月1日的[环境导出](../env/lock/)不包含OpenPI。

以下源码指纹与固定提交的上游文件匹配：

| 文件 | SHA256 |
|---|---|
| `uv.lock` | `793488b5a55bb87200db90a61fd0af51922b686d94e1da4f4c587ab119b37d74` |
| `pyproject.toml` | `e1f457bd81622a47a4c4de17b92815977ac5fcd40116bec92398eb400bf76483` |

历史源码目录为`src/openpi@215abfb2`，不含`.git`。部分文件指纹一致，不等于核验了当前Git HEAD或全部源码。下面的新克隆步骤会保留Git元数据。

## 2. 准备独立服务端环境

先完成[工作目录配置](INSTALL_CN.md#0-工作目录与-miniforge)和[`smolvla`客户端环境](INSTALL_CN.md#3-smolvla-环境smolvlaπ0π05评测与训练共用)。离线评测前还要缓存LIBERO任务与初始状态素材。这里不安装上游LIBERO例子另用的Python 3.8环境。

在Linux工作站使用Bash；每个终端分别设置`REPO`为本仓库绝对路径、`EMB_ROOT`为隔离工作目录。新安装时先定义：

```bash
source "$EMB_ROOT/env.sh"
export OP_REV=215abfb217dbac7d5f1273282331b9b1866c0479
export OP_SRC="$EMB_ROOT/src/openpi@215abfb2"
export OP_ENV="$EMB_ROOT/envs/openpi"
export OP_PY="$EMB_ROOT/envs/openpi_py311/bin/python"
export OP_UV="$EMB_ROOT/envs/openpi_py311/bin/uv"
export UV_CACHE_DIR="$EMB_ROOT/cache/uv"
export UV_PYTHON="$OP_PY" UV_PYTHON_DOWNLOADS=never
export UV_PROJECT_ENVIRONMENT="$OP_ENV" GIT_LFS_SKIP_SMUDGE=1
export OPENPI_DATA_HOME="$EMB_ROOT/cache/openpi"
```

这些变量将Python基础环境、uv环境、下载与缓存放在`EMB_ROOT`内。单独加载`env.sh`不会设置`UV_*`或`OPENPI_DATA_HOME`。已有验收通过的安装应直接复用，不在原目录重跑创建步骤。

**会写环境、下载依赖。** 从任意目录创建Python基础环境并安装原版本uv：

```bash
conda create -y -p "$EMB_ROOT/envs/openpi_py311" -c conda-forge python=3.11.18
"$OP_PY" -m pip install uv==0.9.5
```

`conda`来自前述Miniforge。若固定版本无法解析，停止并记录错误，不静默换Python或改锁文件。历史命令使用`python=3.11`，实际解析为3.11.18；这里将该已解析版本写明。

克隆源码和安装uv的Git依赖都需要Git。工作站默认SSH PATH没有Git，原安装复用了`lerobot`环境中的Git；需要时加入这个已有可执行文件的位置，不安装系统包：

```bash
export PATH="$EMB_ROOT/envs/lerobot/bin:$PATH"
git --version
git clone https://github.com/Physical-Intelligence/openpi.git "$OP_SRC"
git -C "$OP_SRC" checkout --detach "$OP_REV"
cd "$OP_SRC"
sha256sum uv.lock pyproject.toml
"$OP_UV" sync --frozen
```

在sync**之前**将两个哈希与第1节对照。源码目标目录必须未被使用。`sync --frozen`安装到`OP_ENV`，包含可编辑的OpenPI/openpi-client，不会激活客户端环境。安装成功不等于GPU推理通过。此JAX路径不需要上游PyTorch的`transformers_replace`补丁，也不要把服务端依赖装进`smolvla`。

## 3. 原生权重、归一化与分词器

**会下载权重，不做推理。** 准备新的权重目标后，从任意目录运行：

```bash
export OP_CKPT="$EMB_ROOT/ckpt/openpi_pi0_libero"
mkdir -p "$EMB_ROOT/ckpt"
"$OP_PY" "$REPO/scripts/openpi/download_checkpoint.py" \
  checkpoints/pi0_libero "$OP_CKPT"
```

[下载器](../scripts/openpi/download_checkpoint.py)使用公开存储桶，不需要Hugging Face token或`gsutil`。要求末尾为`DONE all md5 verified`；保留权重旁的`openpi_pi0_libero.listing.json`，其中有对象名、大小、更新时间和MD5。历史验收的下载为19个文件、12.01 GB。桶前缀会变化，不是不可变的模型revision，应保留当次清单；本次文档整理没有重算12 GB权重的哈希。

已有且匹配的文件会跳过，不匹配的文件可能被替换。因此它不是对已有验收权重的只读校验工具，不要为了检查安装就原地刷新旧清单。

权重根目录应含`params/`与`assets/physical-intelligence/libero/norm_stats.json`。服务端接收根目录，不是`params/`子目录。原生Orbax参数必须与配套归一化资产一起使用，不使用HF试用检查点的`model.safetensors`。

固定版本的[OpenPI分词器](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/src/openpi/models/tokenizer.py)请求`gs://big_vision/paligemma_tokenizer.model`。按上面的`OPENPI_DATA_HOME`设置，缓存位置为：

```text
$EMB_ROOT/cache/openpi/big_vision/paligemma_tokenizer.model
```

已有安装中存在该文件。新安装可能在加载策略时下载它；完全离线启动需要**权重和这个缓存同时就绪**。`HF_HUB_OFFLINE=1`不能阻断OpenPI的GCS下载器。原生服务端不需要本项目私有/受限的Hugging Face分词器目录，不将分词器凭证或私有材料放入Git。

## 4. 准备客户端的纯配置目录

远程客户端仍会解析`--policy.path`，因此需要有效的PI0 `config.json`。历史目录为`ckpt/pi0_libero_base@98ac51b8_openpi`。同时设置`WRAP=probe`与`POLICY_SERVER`时，[eval_probe.py](../scripts/eval/eval_probe.py)用远程代理替代策略创建、用恒等函数替代前后处理，**不会加载HF试用检查点的PyTorch权重或处理器文件**。

新安装可用下面的命令**只下载小型公开配置**，按历史副本调整dtype字段，并拒绝已有目标。此步骤由源码重建并核对哈希，不是全新机器上的模型实跑；复用既有目录时跳过。

```bash
export OP_CLIENT="$EMB_ROOT/ckpt/pi0_libero_base@98ac51b8_openpi"
"$OP_PY" - <<'PY'
import hashlib
import json
import os
import urllib.request
from pathlib import Path

rev = "98ac51b805725b9f6cc90ad0b92b8b8ecbefa9eb"
url = f"https://huggingface.co/lerobot/pi0_libero_base/resolve/{rev}/config.json"
with urllib.request.urlopen(url, timeout=60) as response:
    raw = response.read()
expected = "80b51238a53ccd8421577e94f39c201915b805c849989558f3c0af410b9a2a5c"
if hashlib.sha256(raw).hexdigest() != expected:
    raise SystemExit("Unexpected source configuration; stop and retain the evidence")
cfg = json.loads(raw)
cfg["dtype"] = "bfloat16"
text = json.dumps(cfg, indent=4)
expected = "2405b602e3b4f3fe8f5e2239e8fa74fad0e69650af2b0fdf8af1c17798669e90"
if hashlib.sha256(text.encode()).hexdigest() != expected:
    raise SystemExit("Configuration differs from the recorded client")
target = Path(os.environ["OP_CLIENT"])
target.mkdir(parents=True, exist_ok=False)
with (target / "config.json").open("x") as output:
    output.write(text)
print("Configuration matches the recorded client")
PY
```

预期字段：`type=pi0`、`chunk_size=50`、两路`[3,256,256]`图像、状态`[8]`、动作`[7]`。CLI将配置中的`n_action_steps=10`覆盖为 **5**。dtype字段属于这个客户端配置；原生模型按OpenPI自身配置加载。无需为了提供代理配置而运行`adapt_openpi_pi0.py`或下载HF试用检查点权重。

## 5. 先启动本机服务端，再运行客户端

**会启动GPU推理与仿真。** 这些是执行说明，本次文档整理没有执行。在同一工作站开两个终端；先查所选端口是否已有服务/任务，不重复启动、不停止其他用户进程。

### 终端A：服务端

恢复第2节变量，按第3节设置`OP_CKPT`并加载`env.sh`。下面的本机共享口令文件**只在不存在时创建一次**：

```bash
"$OP_PY" - <<'PY'
import os
import secrets
from pathlib import Path

os.umask(0o077)
key = Path(os.environ["EMB_ROOT"]) / "tmp/openpi_authkey"
with key.open("x") as output:
    output.write(secrets.token_hex(32))
PY
```

文件已存在会报错；应复用其内容，不在服务端/客户端使用期间重新生成。确认文件可读且非空，读取失败就停止，不继续启动任一进程。不启用shell tracing，也不打印口令。以前台方式启动：

```bash
export OPENPI_PORT=18765
export OPENPI_AUTHKEY="$(cat "$EMB_ROOT/tmp/openpi_authkey")"
"$OP_ENV/bin/python" -u "$REPO/scripts/openpi/serve_pi0_libero.py" \
  "$OP_CKPT" "$OPENPI_PORT"
```

预期出现`loaded ...`及`pi0_libero`对应配置信息，随后`ready on port 18765`；这只说明加载和监听，不代表回合成功。首轮推理可能包含JAX编译。记录运行时应将stdout保存在新的日志中。[本仓库服务桥](../scripts/openpi/serve_pi0_libero.py)使用认证的`multiprocessing.connection`，仅监听 **127.0.0.1**，不是上游OpenPI的WebSocket服务；不能直接换用`serve_policy.py`或把端口开放给外部。

### 终端B：客户端

重新设置`REPO`与`EMB_ROOT`，使用未被占用的运行名：

```bash
source "$EMB_ROOT/env.sh"
export OPENPI_PORT=18765
export OPENPI_AUTHKEY="$(cat "$EMB_ROOT/tmp/openpi_authkey")"
CK="$EMB_ROOT/ckpt/pi0_libero_base@98ac51b8_openpi"
RUN=ojx_smoke_check_01
WRAP=probe BLACKOUT=none POLICY_SERVER="$OPENPI_PORT" \
  bash "$REPO/scripts/eval/run_libero.sh" "$RUN" 5 "$CK" 1 \
  --policy.n_action_steps=5 \
  --env.observation_height=256 --env.observation_width=256
```

入口激活`smolvla`，要求素材已缓存（`HF_HUB_OFFLINE=1`），运行**每任务5回合、共50回合**，batch1、seed1000。`POLICY_SERVER`选择OpenPI原版推理；漏掉它会对这个配置走未通过验收的HF试用路径。已有输出目录/文件/符号链接都会被拒绝，失败工件保留，不删除旧目录绕过保护。

历史协议中，每任务的初始状态序号为：冒烟0–4、门槛0–49、100回合条件0–9。客户端采用280控制步上限，另有10步稳定等待；这与上游示例的220控制步不同。评测seed不会固定独立OpenPI服务端的随机数流。

客户端将两路画面旋转180°，发送原始8维状态与任务文本；服务端缩放到224，使用原归一化并还原增量动作。返回`(50,7)`动作块，执行前5步后重新查询。不要再做一次LeRobot归一化或增量还原。

## 6. 阶段与验收

[run_official_pi0.sh](../scripts/eval/run_official_pi0.sh)封装历史阶段，从[common.sh](../scripts/common.sh)读取端口/口令文件设置，但不会启动服务端。其运行名固定，拒绝原地重跑；获准做独立重复时，应像上例一样通过`run_libero.sh`选择新名字，保持各条件的回合数和参数。

| 阶段 | 运行名 | 每个运行的总回合数 / 渲染 |
|---|---|---|
| `smoke` | `ojx_smoke` | 50 / 256 |
| `gate` | `ojx_none` | 500 / 256 |
| `ablation` | `ojx_all`、`ojx_drop_all`、`ojx_freeze` | 各100 / 256；另含`pi0_drop_all`，100 / 360，走 **LeRobot v044**、不用服务端 |
| `single` | `ojx_drop_wrist`、`ojx_drop_agent` | 各100 / 256 |
| `freeze_wrist` | `ojx_freeze_wrist` | 100 / 256 |
| `res360` | `ojx360_none`、`ojx360_all`、`ojx360_drop_all` | 各100 / 360 |
| `replay` | `ojx360_replay`，然后生成其`replay.json` | 100个来源回合 / 360，再不调用策略地回放固定动作 |
| `conv_smoke`、`conv_diag` | `opi0_*` | HF试用检查点的历史失败诊断；未验证同源，不属于已验收原版路径 |

`ablation`还需要独立的LeRobot v044权重，上面的纯配置目录不提供它。历史回放不是P2：[P2](../scripts/README_CN.md#状态与回放补充实验)使用仓库内冻结动作，不需要OpenPI服务端或重新生成来源。

验收不能只看命令成功：

1. 要求shell退出码0，且`$EMB_ROOT/logs/eval/$RUN/stdout.log`中为`exit=0`。缺失或非零属于技术失败，保留工件。
2. 核对`out/eval_info.json`覆盖十任务且每任务回合数正确。保留`traj.npz`：包装器将首帧哈希存入`h0`，逐步末端记录存入`eef_*`；历史`first_frame_hash.json`/`first_eef.json`是导出文件，不是这个入口自动额外生成的文件。256原版与360 LeRobot画面不能直接比首帧哈希；历史跨分辨率匹配核对的是首步末端位置，不是完整仿真状态。
3. 查`[probe] remote:`中的图像`(224,224,3)`、动作块`(50,7)`与实际掩码。正常时`base_0_rgb`/`left_wrist_0_rgb`为真，空的`right_wrist_0_rgb`为假；`drop_all`三者均为假；黑图保留相机存在掩码；冻结使用真实第1帧、掩码为真。这些干预不等价。
4. 解读消融前，**人工核对正常500回合门槛≥92%**。将上例每任务数量5改为50，并另选新名字。分阶段脚本会传播命令失败，**不会自动执行成功率门槛**；不能反复挑选、丢弃状态来达到预期分数。

历史已验收原版结果包括冒烟50/50、门槛482/500、256全黑0/100和两路槽位屏蔽0/100，见[完整表格与局限](EXPERIMENTS_CN.md#15-官方-π0-对照)及[原始记录](../dashboard/data/official_pi0/)。原版某步动作超出`[-1,1]`本身不是门槛失败：该早期规则已在日志更正，不额外裁剪动作强行满足它。

100回合条件使用每任务前10个初始状态，正常配对子集是93/100，不能拿完整门槛的96.4%替代；360复测另列。服务端随机数流和其他非确定性使重复分数不保证逐位相同。这些结果仍不能将权重与推理管线差异分离，也未识别LeRobot v044残余成功的唯一机制。

## 7. 故障核对与证据入口

| 现象 | 再次启动前核对 |
|---|---|
| 安装时找不到`git` | 查PATH；历史安装复用了`envs/lerobot/bin/git` |
| 无法导入`openpi` | 使用`OP_ENV/bin/python`，核对可编辑源码位置和固定锁安装，不向客户端补装 |
| 离线加载策略卡住/失败 | 查原生参数、归一化资产及独立OpenPI分词器缓存；HF离线设置不够 |
| 连接拒绝或认证失败 | 查现有服务是否ready、本机端口和口令文件是否一致，不打印口令 |
| `Address already in use` | 查已有占用者，不重复起服务、不终止其他任务 |
| 输出已存在 | 换新的运行名，保留旧结果和失败记录 |
| 客户端没有`remote:`证据 | 查`WRAP=probe`、`POLICY_SERVER`、batch1及有效客户端配置，不能按原版OpenPI验收 |
| exit0但成功率低 | 查覆盖、版本、图像/掩码证据与预处理，保留负结果，不改称复现成功 |

这些是基于源码的核对项，不表示每种故障都在新运行中出现过。本次文档整理未重新验证GPU显存可用性或新机器启动。

历史安装/下载/服务日志位于`$EMB_ROOT/logs/official/`，下载清单位于权重旁。公开证据见[实验日志](NOTES_CN.md)、[官方结果CSV](../results/official_pi0_summary.csv)和[原始JSON](../dashboard/data/official_pi0/)。Git不包含完整权重、口令、分词器文件或私有日志。只想重算公开表格时，使用[无需模型和仿真的CPU快速开始](../README_CN.md#快速开始)。

固定版本上游依据：[安装及JAX/PyTorch区别](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/README.md)、[依赖定义](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/pyproject.toml)、[锁文件](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/uv.lock)、[LIBERO例子](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/examples/libero/README.md)、[缓存实现](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/src/openpi/shared/download.py)、[客户端配置来源](https://huggingface.co/lerobot/pi0_libero_base/blob/98ac51b805725b9f6cc90ad0b92b8b8ecbefa9eb/config.json)。
