# 脚本索引

[English](README.md) · [项目首页](../README_CN.md) · [文档导航](../docs/README_CN.md)

从要复现的结果选择入口。以下表格链接到源文件；带参数入口的用法以文件开头和运行时提示为准。相对路径按仓库根目录解释。

## 先准备什么

只重算已有数据时不需要模型、EGL或`EMB_ROOT`；按照[首页快速开始](../README_CN.md#快速开始)准备NumPy分析环境。以下配置仅用于实际评测。

先完成[安装](../docs/INSTALL_CN.md)和[环境配置](../env/README_CN.md)，设置 `EMB_ROOT` 并准备相应权重。Shell 评测入口加载 [common.sh](common.sh)，再读取 `$EMB_ROOT/env.sh` 与本地权重路径。

评测包装器通过运行时替换函数实现干预，不修改 LeRobot / OpenVLA 源码。需要 GPU 或模型前向的入口与只处理已有数据的分析脚本分开列在下面。

运行入口以原子方式创建新目录；同名目录、文件或链接（含失效链接）均拒绝使用，失败后的目录也保留。运行名只接受字母、数字、下划线、连字符和点，不能是`.`、`..`或路径。`run_libero.sh`和`run_train.sh`的额外参数不能覆盖`--output_dir`。

执行命令的退出码会保留并写入`stdout.log`的`exit=<code>`；批量入口遇到必需子任务失败会返回非零，不写成功完成标记。历史训练流程仍保留原有batch16失败后尝试batch8的测速回退。并行/训练流水线会保留`.*.started`目录作为启动记录，并拒绝覆盖已有结果、共享日志和完成标记，不能原地重复启动。

ACT的新输出统一为`logs/eval/act_cube_500/stdout.log`与`out/`；旧`logs/act_500.log`保持不动。需要重复LIBERO、OpenVLA评测或训练时，使用相应带运行名的入口选择新名字。ACT、DP及批量入口使用固定名字，会拒绝在原位置重跑；不要删除旧工件来绕过保护。

## 公开权重复现

| 模型 / 任务 | 入口 | 汇总 |
|---|---|---|
| ACT · ALOHA Transfer Cube | [run_act.sh](eval/run_act.sh) | [summarize_eval.py](analysis/summarize_eval.py) |
| Diffusion Policy · PushT | [run_dp_pusht.sh](eval/run_dp_pusht.sh) | [summarize_eval.py](analysis/summarize_eval.py) |
| OpenVLA · LIBERO-Spatial | [run_ovla.sh](eval/run_ovla.sh) | [ovla_to_json.py](analysis/ovla_to_json.py) |
| SmolVLA / π0 / π0.5 · LIBERO-Spatial | [run_libero.sh](eval/run_libero.sh) | [summarize_eval.py](analysis/summarize_eval.py) |

`run_libero.sh` 的参数依次是运行名、每任务回合数、权重目录、batch size，后面可追加评测参数。10 个 LIBERO 任务各 50 回合即为 500 回合。

复现表中的 SmolVLA 是 `lerobot/smolvla_libero`。额外参数在 `common.sh` 的 `SMOL2_ARGS` 中定义：

- `--policy.n_action_steps=10`。
- `--rename_map` 把 `observation.images.image` / `image2` 映射到 `observation.images.camera1` / `camera2`。
- 底座 `HuggingFaceTB/SmolVLM2-500M-Video-Instruct`必须按[离线准备](../docs/INSTALL_CN.md#41-离线评测前准备)缓存固定revision，并核对本地main别名。

## 转换与汇总已有结果

以下工具只处理已有文件，不加载模型或仿真。按运行名查找时需要`EMB_ROOT`；`summarize_eval.py --file`可直接读取指定JSON，无需工作站环境。

```bash
RUN=openvla_spatial_500
python scripts/analysis/ovla_to_json.py "$RUN" novideo
python scripts/analysis/summarize_eval.py --file \
  "$EMB_ROOT/logs/eval/$RUN/dash/eval_info.json"
```

从仓库根目录执行。第一步读取`logs/eval/$RUN/logs/`下唯一的`.txt`，验证逐回合Task/video/Success记录，再创建新的`dash/`；`novideo`只省略视频复制。省略它会挑选每任务第一段成功/失败视频，预先检查所选文件存在。输出JSON最后写出，复制失败时保留已创建的失败目录和工件。

已有目录、文件或链接（含失效链接）一律拒绝，不删除旧`dash/`。需要重新转换时，传`--output "$EMB_ROOT/logs/eval/$RUN/dash_check_01"`等未用目录；有多个日志时用`--log FILE`显式选择，不静默取第一个。异常记录、空日志、未完成的逐回合块都会报错；仍需人工核对预定任务/回合覆盖和原评测退出码，完整块也可能只来自部分运行。

原来的`python scripts/analysis/summarize_eval.py RUN [RUN ...]`调用仍可用；每个运行必须只有一份`eval_info.json`，多份时改用`--file PATH`。工具核对总体次数/成功率与逐任务结果一致，允许OpenVLA转换结果省略耗时字段。

退出码：**0**表示所选输入均处理成功，**1**表示输入缺失、歧义、数据不合法或读写失败，**2**表示参数/所需环境配置错误。批量汇总中有效运行仍会显示，但任一失败使总退出码为1。区间保留历史二项正态近似；官方Wilson区间、P1/P2配对bootstrap应看对应专用结果，不把通用汇总当作实验验收门槛。

## 相机消融与官方 π0

| 实验 | 入口 | 结果与解释 |
|---|---|---|
| 四种模型全涂黑 | [run_blackout_all.sh](eval/run_blackout_all.sh) | [summarize_blackout.py](analysis/summarize_blackout.py) · [实验 1.1](../docs/EXPERIMENTS_CN.md#11-所有相机涂黑) |
| 加噪声、冻结首帧 | [run_perturbation.sh](eval/run_perturbation.sh) | [实验 1.2](../docs/EXPERIMENTS_CN.md#12-单路相机噪声冻结画面) |
| 末端轨迹、单路相机涂黑 | [run_trajectory_and_single_camera.sh](eval/run_trajectory_and_single_camera.sh) | [轨迹分析](analysis/analyze_trajectories.py) · [单路汇总](analysis/summarize_single_camera.py) |
| 官方 π0 对照、单路屏蔽、冻结与回放 | [run_official_pi0.sh](eval/run_official_pi0.sh) | [实验 1.5–1.6](../docs/EXPERIMENTS_CN.md#15-官方-π0-对照) |

按[官方OpenPI安装与复现指南](../docs/OPENPI_CN.md)准备独立JAX环境、原生权重/分词器缓存、纯配置客户端及本机[serve_pi0_libero.py](openpi/serve_pi0_libero.py)服务；[download_checkpoint.py](openpi/download_checkpoint.py)负责原生资产下载。

指南逐项对应历史阶段的运行名、回合数与渲染设置。入口不会启动服务，也不自动执行≥92%的成功率门槛，需核对工件后验收。早期HF试用检查点失败且未验证与原生权重同源，不能把它作为同权重的管线对照，见[证据核验](../dashboard/data/protocol_audit/)。

`summarize_blackout.py`只汇总原有固定运行：每任务50回合正常、10回合全黑，正常取前10回合。它检查唯一输入、十任务及完整回合覆盖，复用严格OpenVLA日志解析；空日志、异常、截断和歧义输入返回1，不输出成功汇总。默认写入新的`$EMB_ROOT/logs/eval/B_summary.json`；已有输出会被拒绝，可用`--output`选择未用JSON路径。参数/环境错误返回2。它不替代种子、初始状态哈希和原评测退出码的验收。

## 最小相机评测

在已完成安装与权重准备的环境中，从隔离仓库副本根目录运行。`EMB_ROOT`必须已设置：

```bash
CK="$EMB_ROOT/ckpt/pi0_libero_finetuned_v044@45dcc8fc"
RUN=pi0_camera_black_smoke
WRAP=probe BLACKOUT=all bash scripts/eval/run_libero.sh \
  "$RUN" 1 "$CK" 1 --policy.n_action_steps=5 \
  --env.observation_height=360 --env.observation_width=360 \
  --env.max_parallel_tasks=1
```

`CK`定位权重；`RUN`指定本次独立输出，必须未被使用；入口本身会原子拒绝重复启动。
评测每任务1回合、十任务共10回合，batch1、每次执行5步动作，模型接收全黑图；它只检查入口，不是新的成功率基准。
输出在`$EMB_ROOT/logs/eval/$RUN/`，外层退出码必须为0，同时检查`stdout.log`里的`exit=0`和`out/eval_info.json`的10回合覆盖；命令成功不等于结果已验收。
缺环境、权重或EGL时按[排错](../docs/TROUBLESHOOTING_CN.md)处理；不要覆盖旧结果或盲目重跑。

## 状态与回放补充实验

| 目的 | 入口 | 要求与产物 |
|---|---|---|
| 重算已完成P1/P2 | [summarize_followup.py](analysis/summarize_followup.py) | NumPy；无需模型/GPU；生成6个CSV、中英文统计图与网页摘要数据 |
| 重复P1状态输入评测 | [run_state_feedback.py](eval/run_state_feedback.py) → [eval_state_feedback.py](eval/eval_state_feedback.py) | 已配置模型/EGL环境；40工程＋1200正式回合；逐阶段验收 |
| 重复P2冻结动作回放 | [replay_holdout.py](analysis/replay_holdout.py) | 已配置LIBERO/MuJoCo 3.3.2/EGL；10自回放通过至少8个后才执行400正式回合；不加载策略 |

### P1启动步骤：仅供获准的独立重复

先完成[离线准备](../docs/INSTALL_CN.md#41-离线评测前准备)中的LeRobot π0 v044权重、本地分词器及LIBERO素材配置，不需要运行SmolVLA底座下载块。此入口使用当前Python解释器，不自动加载`env.sh`或激活conda环境；应在Linux工作站显式激活`smolvla`。`REPO`是本仓库绝对路径，`EMB_ROOT`是已配置工作目录。

**下面会启动40工程＋1200正式回合，使用模型/GPU和仿真；本次文档整理未执行。** 只有获准重复时才运行，不用于单纯重算公开统计。选未使用的运行前缀和独立JOB目录，从任意目录执行：

```bash
(
  set -e
  source "$EMB_ROOT/env.sh"
  conda activate smolvla
  export HF_HUB_CACHE="$HF_HOME/hub"
  export STATE_RUN_PREFIX=statefb_repeat_01
  P1_JOB="$EMB_ROOT/tmp/$STATE_RUN_PREFIX"
  mkdir -- "$P1_JOB"
  cp -R -- "$REPO/scripts" "$P1_JOB/scripts"
  mkdir -p -- "$EMB_ROOT/logs/eval"
  python -u "$P1_JOB/scripts/eval/run_state_feedback.py" > "$P1_JOB/pipeline.log" 2>&1
)
```

`set -e`使准备失败就停止；子Shell不改变当前终端的激活状态。`mkdir`拒绝已有JOB，复制完整`scripts/`后入口才可定位同级包装器。只复制公开脚本，不复制权重、分词器或论文。日志父目录在运行前创建；各组输出仍由原入口独占创建。

预期JOB中出现`manifest.json`、`started.flag`、`smoke_pass.flag`、`r0_pass.flag`、`r1_pass.flag`、`r2_pass.flag`和最终`done.flag`；外层退出码须为0。16个分组运行位于`logs/eval/${STATE_RUN_PREFIX}_{smoke,r0,r1,r2}_{A,B,C,D}/`。每组检查`exit_code`为0（这里不是Shell包装器的`stdout.log`末行`exit=0`）、`out/eval_info.json`、`evidence.json`、`traj.npz`及状态NPZ。工程检查每组10回合，三轮正式每组100回合；保持360渲染、每次执行5步、seed1000及原分组/配对判据。

入口按工程检查→交叉配对→三轮正式推进，任一技术/证据门槛失败即停止。失败目录和标记保留；只换`STATE_RUN_PREFIX`不能绕过同一JOB的`started.flag`，应核查原因后另选JOB和前缀，不删除标记重跑。它依赖已有配置环境；文档命令仅静态核对，不声称新机器或本次模型运行通过。恢复实验与P3继续暂停。

### P2冻结动作回放

P2十条选定动作已保真导出在[data/replay_holdout](../dashboard/data/replay_holdout/)，不需要OpenPI服务或重新生成来源动作。
需要有界入口检查时，在已激活的隔离仿真环境和仓库根目录运行：

```bash
python scripts/analysis/replay_holdout.py \
  --output "$EMB_ROOT/logs/eval/p2_self_check" --self-only
```

`--self-only`只跑十个自回放并核对原至少8/10门槛，随后结束。检查`runtime.json`中的`mode: self_only`、`self_gate.json`、`progress.json`中的`status: self_completed`及`self_done.json`；正式结果必须为空，且不得出现`done.json`。它不复测400目标结果；门槛失败返回非零，保留工件而不写完成标记。输出名必须未被使用。

不加这个参数时，下列命令会运行完整410回合；不是离线统计命令：

```bash
python scripts/analysis/replay_holdout.py \
  --output "$EMB_ROOT/logs/eval/p2_replay_check"
```

`--output`必须不存在；查看`self_gate.json`、`progress.json`、`done.json`与实际异常。技术失败单列并停止，不重选动作。
打包入口沿用已验收P2的回放循环。
完整逐步NPZ只写新输出目录、不入Git；内置的[公开结果](../results/README_CN.md)不会被覆盖。
恢复实验和原五步延迟P3不在本轮运行范围内。

2026-11-01已在既有环境实跑打包后的`--self-only`入口，自回放10/10，动作前缀精确核对通过，正式回合为0；上方最小相机示例也通过十回合工程检查及输出保留核验。这不代表干净安装验收、完整P2复测或新增正式样本，详见[安装验证范围](../docs/INSTALL_CN.md#7-验证范围)。

## 干预怎样配置

[run_libero.sh](eval/run_libero.sh) 的 `WRAP` 选择实际评测入口：

| `WRAP` | 入口 | `BLACKOUT` |
|---|---|---|
| `none`（默认） | `lerobot-eval` | 不做相机干预 |
| `blackout` | [eval_blackout.py](eval/eval_blackout.py) | `all`、`agent`、`wrist` |
| `probe` | [eval_probe.py](eval/eval_probe.py) | 见下方；额外记录 `traj.npz` |

`probe` 支持 `none`、`all`、`agent`、`wrist`、`noise`、`freeze`、`drop_wrist`、`drop_agent`、`drop_all`、`freeze_wrist`、`freeze_agent`。

`drop_*` 在原槽位屏蔽相机，不是从字典删键；`freeze_*` 使用本回合第一帧。具体模型支持范围和掩码验收以包装器断言为准。干预不可互相替代，比较口径见[实验说明](../docs/EXPERIMENTS_CN.md)。

## 已有数据的分析与出图

| 目的 | 入口 | 输入要求 |
|---|---|---|
| 重建看板数据 | [dashboard/build.py](../dashboard/build.py) | 仓库内原始评测 JSON；标准库 |
| 生成 CSV / 中英文 SVG | [make_figures.py](analysis/make_figures.py) | 看板数据与已收录的轨迹摘要；标准库 |
| 比较末端轨迹 | [analyze_trajectories.py](analysis/analyze_trajectories.py) | 原始 `traj.npz` 与 NumPy |
| 导出任务 4 / 7 的图件数据 | [export_trajectories.py](analysis/export_trajectories.py) | 原始 `traj.npz` 与 NumPy |
| 逐帧比较视频 | [compare_videos.py](analysis/compare_videos.py) | 对应运行的录像 |
| 指标实现 | [metrics.py](analysis/metrics.py) | CI、两比例检验、DTW 与抓取点；由 [tests/](../tests/) 核验 |

相机评测新结果接入：把评测输出中的 `eval_info.json` 放到 `dashboard/data/<run>/`，在 `dashboard/build.py` 注册对应运行，再依次执行下列命令。官方对照等专题汇总还需提供对应的配对/哈希记录，不能只填一个成功率。

```bash
python3 dashboard/build.py
python3 scripts/analysis/make_figures.py
python3 scripts/analysis/summarize_followup.py
```

三条命令在仓库根目录执行，依次更新看板数据、原有图表与P1/P2统计；第三条需要NumPy。[结果目录](../results/README_CN.md)列出产物，[CI](../.github/workflows/ci.yml)核对生成一致性。

## 自检、诊断与历史实验

- **既有协议补证：** [summarize_protocol_audit.py](analysis/summarize_protocol_audit.py)只读核查95条来源关联元数据、公开结果/长度文件哈希与220步截止计分，CI不重新读取Git外原始工件；`--write`仅重建补充CSV。[check_checkpoint_identity.py](analysis/check_checkpoint_identity.py)在已有OpenPI环境中用CPU核对原生/HF参数，不导入模型、不写权重；返回1表示已确认参数不同，返回2表示不完整或输入错误。输入、内存保护和命令见[证据说明](../dashboard/data/protocol_audit/)。
- **A0元数据检查：** 上述协议检查同时核对载入报告的逐项差异、覆盖、别名、dtype/形状、输入指纹及CPU执行范围；不重新加载模型或核验Git外原报告。[语义检查实现](analysis/validate_loading_audit.py)。
- **公开仓库检查：** [repository_check.py](checks/repository_check.py)离线检查Git跟踪的相对链接/锚点、JavaScript语法（需Node.js）和引用/项目版本；现有CI会执行，不导入模型或仿真。
- **旧ACT演示导出：** [export_act.py](../viewer/export_act.py)使用已配置`lerobot`环境及未被使用的`--output`目录；顺序尝试seed1000–1009，取首个成功演示或最后一次失败，不属于评测结果。已有输出和失败工件均保留。另获准导出后，将`done.json`指向的`.mjb`及选中`.npz`一起复制到本地查看器；[replay.py](../viewer/replay.py)头部有macOS的`mjpython`命令。本轮维护未在GPU上运行该导出器。

- **LIBERO离线素材：** [libero_assets_check.py](checks/libero_assets_check.py)只读检查hf-libero 0.1.4的Spatial文件及素材目录，不导入仿真器；[首次准备步骤](../docs/INSTALL_CN.md#42-准备-libero-仿真素材)。
- **环境自检：** [torch_check.py](checks/torch_check.py)、[egl_smoke.py](checks/egl_smoke.py)、[codec_check.py](checks/codec_check.py)，分别检查 GPU/torch、EGL 与视频解码。
- **π0 诊断：** [run_pi0_full.sh](eval/run_pi0_full.sh) 与 [run_pi0_action_steps.sh](eval/run_pi0_action_steps.sh)，对应历史冒烟、完整评测和动作块长度检查。
- **历史微调：** [run_statedrop_pipeline.sh](train/run_statedrop_pipeline.sh) 调用 [run_train.sh](train/run_train.sh)，由 [summarize_statedrop.py](analysis/summarize_statedrop.py) 汇总。结果与后续更正保留在[实验日志](../docs/NOTES_CN.md)，不作为 README 的主要发现。
