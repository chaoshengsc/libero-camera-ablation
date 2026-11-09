# 换设备后继续相机实验需要准备运行环境与模型资产

[English](CONTINUE.md) · [项目首页](../README_CN.md) · [安装说明](INSTALL_CN.md)

本仓库包含公开结果、评测代码、运行配置记录和安装说明。拉取后可以准备统计重算；继续运行模型还需要所选环境、权重、分词器和仿真素材。当前参考路径是既有Ubuntu 24.04／NVIDIA环境，尚未在新设备上完成从安装到闭环运行的验收；Windows和macOS的完整仿真路径未验证。

## 不同目标需要不同材料

| 目标 | 必需材料 | 当前状态 |
|---|---|---|
| 重算公开结果与图表 | 仓库、Python 3.10+、NumPy | 公开记录已齐备，不需模型或GPU；见[快速开始](../README_CN.md#快速开始) |
| 继续新的相机评测 | 固定源码、对应环境、模型与处理器、LIBERO任务／初态／assets、新正常组和独立输出 | 代码与重建说明已公开，目标设备上的准备和运行仍需验收 |
| 重做旧完整行为审计 | 旧NPZ、原日志、录像及对应审计输入 | 完整工件留在Git外；曾未保存的图像／终止字段无法补回 |

旧完整NPZ不是继续新增相机实验的前置条件。公开结果JSON也不能替代模型权重和仿真素材。

## 运行材料按模型分别准备

| 路径 | 必需资产与配置 | 准备入口 |
|---|---|---|
| LeRobot π0／π0.5 | 对应v044权重、归一化／预处理文件、获授权的PaliGemma分词器；本地分词器路径须在新设备重设 | [安装](INSTALL_CN.md)，只需所选模型的环境，不需ACT／DP或训练数据 |
| SmolVLA | 策略权重、固定SmolVLM2底座及processor缓存、相机rename映射 | [离线准备](INSTALL_CN.md#41-离线评测前准备) · [脚本参数](../scripts/README_CN.md#公开权重复现) |
| OpenVLA | 独立Python环境、固定OpenVLA与原始LIBERO源码、模型权重、任务／初态和素材 | [OpenVLA安装](INSTALL_CN.md#2-openvla-环境) |
| 官方π0／OpenPI | 独立JAX环境、原生Orbax检查点、norm_stats、GCS分词器缓存，以及纯配置客户端 | [OpenPI指南](OPENPI_CN.md)；不能用失败HF候选替代原生权重 |
| P2固定动作回放 | 仿真环境、任务／初态／素材、公开冻结动作与选择记录 | [回放输入](../dashboard/data/replay_holdout/README.md)；不调用策略模型 |

固定源码和模型revision见[安装说明](INSTALL_CN.md)、[通用配置](../scripts/common.sh)与[运行清单](../configs/camera_study_runs.json)。权重、受限分词器和凭证不放入Git。原生GCS权重前缀可能变化；要确认与旧权重相同，需核对既有下载清单或独立保留的内容哈希，不能只凭同名路径。

LIBERO还需要BDDL任务、`.pruned_init`初态和网格／纹理assets。指南固定了后续安装素材快照，未确认历史assets的完整revision。需要贴近旧环境时，应另行备份原任务／初态／assets及内容清单。普通评测不需下载示范训练数据。[素材准备与检查](INSTALL_CN.md#42-准备-libero-仿真素材)按默认布局检查文件存在，不能代替自定义配置、内容哈希或渲染验收。

环境目录是[样例和历史清单](../env/README_CN.md)，不是可直接搬到另一系统的已验收安装。OpenPI独立环境不在三个旧conda导出中。历史`eval_ft*`和训练脚本保留旧诊断；它们不属于本轮独立微调项目，也不进入相机证据冻结清单。

## 十一组500回合历史记录有独立配置索引

[JSON清单](../configs/camera_study_runs.json)区分历史记录、未来运行配方与未启动计划。各历史运行都是10任务×50初态、batch1、seed1000、预测50步、内部迭代10次、280控制步；π0执行5步后重推理，π0.5执行10步。逐组设置来源是[provenance](../dashboard/data/protocol_audit/provenance.json)。

| 历史记录 | 干预 | 已公开分析的正常参照 |
|---|---|---|
| `s500/pi05_none` | 正常 | `s500/pi05_none` |
| `s500/pi05_drop_wrist` | 腕部mask | `s500/pi05_none` |
| `s500/pi05_freeze_wrist` | 腕部首帧冻结 | `s500/pi05_none` |
| `s500/pi05_drop_agent` | 主视角mask | `s500/pi05_none` |
| `s500/pi0_none` | 正常 | `s500/pi0_none` |
| `s500/pi0_none_r2` | 正常 | `s500/pi0_none` |
| `s500/pi0_wrist` | 腕部黑图 | `s500/pi0_none` |
| `s500/pi0_drop_wrist` | 腕部mask | `s500/pi0_none` |
| `s500/pi0_drop_wrist_r2` | 腕部mask | `s500/pi0_none` |
| `s500/pi0_freeze_wrist` | 腕部首帧冻结 | `s500/pi0_none` |
| `s500/pi0_drop_agent` | 主视角mask | `s500/pi0_none` |

这里的正常参照沿用已公开统计；`r2`不证明两组是同期配对。历史导出明确记录height360，未单列width；清单用null表示未知。未来命令显式设360×360和280步，不把它们追认为已恢复的完整历史CLI。

π0.5腕部黑图另外引用历史同100初态的5次执行，不在这11组500初态新运行中。任务／初态索引与首帧hash匹配不代表完整状态或策略噪声逐位相同。

## 命令生成器只输出一组选定配置

在拉取后的仓库根目录使用Python 3.10+，无需第三方库。以下只列出配置或打印命令，不执行命令、不加载模型、不写运行目录：

```bash
python scripts/eval/camera_study_commands.py --list
python scripts/eval/camera_study_commands.py   --run s500/pi05_drop_wrist --new-run-name pi05_wrist_mask_new_01   --emb-root /path/to/new/workdir --smoke
```

第二条生成每任务1回合、共10回合的工程检查命令。完成下面的目标设备验收后，去掉`--smoke`会生成每任务50回合、共500回合的命令；两种情况都只打印，须人工审阅后另行执行。生成命令会清除继承的`POLICY_SERVER`和`OPENPI_AUTHKEY`，并固定`DELTA_REF=chunk`，避免意外切到OpenPI桥接或旧诊断设置。运行路径与权重位置由目标设备的`EMB_ROOT`生成。新运行名必须未使用，已有输出不覆盖。

先用`s500/pi05_none`生成新正常组，再选择目标干预；每次使用新的运行名，并记录新正常／干预对应关系。π0选对应的`pi0_*`模板。历史正常列不能自动成为新设备的配对基线。未做的主视角冻结、主实验规模黑图与π0.5双路mask仍是[后续计划](STUDY_MAP_CN.md#后续将补齐尚未完成的适用对照)，清单列出其状态，不自动启动。

## 目标设备验收分阶段完成

| 阶段 | 通过依据 | 目前状态 |
|---|---|---|
| 仓库材料核验 | 指定Git提交、[207份证据校验](../scripts/checks/freeze_check.py)、配置与公开来源一致 | 仓库侧检查已具备 |
| 本地准备核验 | 所选源码／包版本、权重与处理器、有效缓存路径、任务／初态／assets、新输出位置 | 待设备确定后执行 |
| 运行工程验收 | 正常／目标干预各十回合，实际退出0、十任务覆盖、有限动作、干预生效与初态配对记录 | 新设备尚未验收 |
| 正式实验 | 预先固定正常组、干预、任务／初态、seed、回合数与停止条件，保留完整新运行记录 | 按具体实验另行执行 |

`torch_check.py`会执行CUDA运算；`egl_smoke.py`运行ALOHA并写图；`codec_check.py`写临时视频，不能把这些称为只读LIBERO检查。GPU、渲染、推理及闭环验收应在选定目标设备后分别记录。十回合工程通过不等于完整成功率复现。

新运行至少保留实际命令／环境变量、源码与包版本、模型revision及处理器配置、素材／初态清单、任务与初态索引、正常组映射、退出码、逐回合成功与结束原因、首帧匹配见证及运行工件。发生错误保留失败目录，使用新运行名排查；结果登记和重算见[脚本索引](../scripts/README_CN.md#已有数据的分析与出图)。
