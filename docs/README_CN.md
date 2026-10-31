# 文档导航

[English](README.md) · [项目首页](../README_CN.md) · [交互结果页](https://chaoshengsc.github.io/libero-camera-ablation/dashboard/?lang=zh)

README 给出主要结论；这里按阅读、复现与核查组织完整材料。实验日志保留历史判断和后续更正，当前结果以实验说明及原始证据为准。

| 目的 | 文档 | 内容 |
|---|---|---|
| 理解实验 | [实验设计与完整结果](EXPERIMENTS_CN.md) | 干预定义、全部表格、重复运行与解释边界 |
| 配置环境 | [安装指南](INSTALL_CN.md) | 环境、权重、分词器与第一条评测命令 |
| 选择入口 | [脚本索引](../scripts/README_CN.md) | 复现、相机消融、官方 π0 与分析脚本 |
| 解决故障 | [排错文档](TROUBLESHOOTING_CN.md) | 按现象查原因和处理步骤 |
| 核对数字 | [结果目录](../results/README_CN.md) | CSV 字段用途、原始证据与生成入口 |
| 追溯过程 | [实验日志与更正](NOTES_CN.md) | 按时间保留的设计、失败、修订与运行记录 |

## 常用路径

- **先理解结论：** [README](../README_CN.md) → [完整实验](EXPERIMENTS_CN.md) → [局限](../README_CN.md#局限)。
- **复现一个模型：** [安装](INSTALL_CN.md) → [环境目录](../env/README_CN.md) → [脚本索引](../scripts/README_CN.md)。
- **核对一个数字：** [结果 CSV](../results/README_CN.md) → [原始评测](../dashboard/data/) → [对应实验与更正](NOTES_CN.md)。

## 实验与证据对应

| 实验说明 | 结果表 | 原始证据入口 |
|---|---|---|
| [全涂黑](EXPERIMENTS_CN.md#11-所有相机涂黑) | [blackout_per_task.csv](../results/blackout_per_task.csv) | [原始记录](../dashboard/data/) |
| [噪声与冻结](EXPERIMENTS_CN.md#12-单路相机噪声冻结画面) | [perturbations.csv](../results/perturbations.csv) | [原始记录](../dashboard/data/run2/) |
| [轨迹比较](EXPERIMENTS_CN.md#13-看不见的-π0-在成功的任务上走的是同一条路线) | [trajectory.csv](../results/trajectory.csv) | [原始记录](../dashboard/data/traj_analyze.json) |
| [单路相机](EXPERIMENTS_CN.md#14-只去掉腕部相机500-回合) | [single_camera_summary.csv](../results/single_camera_summary.csv) | [原始记录](../dashboard/data/s500/) |
| [官方 π0](EXPERIMENTS_CN.md#15-官方-π0-对照) | [official_pi0_summary.csv](../results/official_pi0_summary.csv) | [原始记录](../dashboard/data/official_pi0/) |
| [固定动作回放](EXPERIMENTS_CN.md#16-固定动作回放) | [open_loop_replay.csv](../results/open_loop_replay.csv) | [原始记录](../dashboard/data/official_pi0/ojx360_replay/replay.json) |
| [公开权重复现](EXPERIMENTS_CN.md#2-公开权重的复现) | [reproduction.csv](../results/reproduction.csv) | [原始记录](../dashboard/build.py) |

## 怎样更新结果

在仓库根目录先运行 `python3 dashboard/build.py`，再运行 `python3 scripts/analysis/make_figures.py`；分别更新看板数据、CSV 与中英文 SVG，不执行模型评测。

[tests/](../tests/) 和 [CI](../.github/workflows/ci.yml)核对派生数字与原始记录的一致性。新增一组结果的执行入口与数据接入方式见[脚本索引](../scripts/README_CN.md)。

<details>
<summary>历史更新与更正</summary>

- **2026-10-29** · 官方 π0 对照（[1.5 节](EXPERIMENTS_CN.md#15-官方-π0-对照)）：OpenPI 原版正常 96.4%，去掉视觉后 0%；只屏蔽腕部 0%，只屏蔽主视角 77%。旧版说 LeRobot π0 权重“训练不足”，本仓库没有检验过这一点，已改为陈述事实。
- **2026-10-28** · 单相机实验，每个条件 500 回合（[1.4 节](EXPERIMENTS_CN.md#14-只去掉腕部相机500-回合)）。搭实验时发现 LeRobot 在缺一路相机时会悄悄错位相机槽位：已报告为 [lerobot#5118](https://github.com/huggingface/lerobot/issues/5118)，修复提交为 [lerobot#5129](https://github.com/huggingface/lerobot/pull/5129)。
- **2026-10-14** · [v1.3](https://github.com/chaoshengsc/libero-camera-ablation/releases/tag/v1.3)：所有消融各重跑一次；撤回了“π0 依赖腕部相机”的结论。
- **2026-10-07** · [v1.2](https://github.com/chaoshengsc/libero-camera-ablation/releases/tag/v1.2)：仓库改名；SmolVLA 消融改用复现表里的同一个权重重跑。

</details>
