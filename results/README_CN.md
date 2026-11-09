# 结果目录

[English](README.md) · [项目首页](../README_CN.md) · [文档导航](../docs/README_CN.md)

这里保存可重算的结果表；方法、比较范围与判读见[实验说明](../docs/EXPERIMENTS_CN.md)，原始评测在 [dashboard/data/](../dashboard/data/)。

[2026-11-09 冻结说明](../docs/FREEZE_CN.md) · [证据 SHA-256 清单](freeze_20261109_v1.5.2.sha256)。在仓库根目录运行 `python scripts/checks/freeze_check.py`，只读核对公开证据文件。

## 按实验找结果

| 文件 | 内容 |
|---|---|
| [reproduction.csv](reproduction.csv) | 五个公开权重、基准与置信区间 |
| [blackout_per_task.csv](blackout_per_task.csv) | 四种模型全涂黑前后的逐任务成功次数 |
| [perturbations.csv](perturbations.csv) | 噪声、冻结、单路涂黑与重复运行 |
| [trajectory.csv](trajectory.csv) | 两次轨迹比较、DTW 与抓取点差异 |
| [single_camera_summary.csv](single_camera_summary.csv) | 500 回合单路相机汇总与配对统计 |
| [single_camera.csv](single_camera.csv) | 单路相机逐回合成功标记与首帧哈希 |
| [official_pi0_matched100.csv](official_pi0_matched100.csv) | 每任务前10初态的100回合子集，保留来源运行和每次重复；官方图使用此表 |
| [official_pi0_summary.csv](official_pi0_summary.csv) | 官方/OpenPI、LeRobot 与渲染对照 |
| [open_loop_replay.csv](open_loop_replay.csv) | 自回放、交叉回放与事后挑选偏差 |
| [state_feedback_episodes.csv](state_feedback_episodes.csv) | P1全部1240回合，明确smoke/正式与状态配对 |
| [state_feedback_runs.csv](state_feedback_runs.csv) | P1逐组/逐轮计数及Wilson区间 |
| [state_feedback_per_task.csv](state_feedback_per_task.csv) | P1逐任务/条件/重复计数 |
| [state_feedback_comparisons.csv](state_feedback_comparisons.csv) | P1预定主比较、次比较与探索性交互 |
| [replay_holdout_episodes.csv](replay_holdout_episodes.csv) | P2全部410个自回放/正式结果，含结束原因 |
| [replay_holdout_summary.csv](replay_holdout_summary.csv) | P2逐任务Wilson与总体分层bootstrap区间 |
| [budget_sensitivity.csv](budget_sensitivity.csv) | 既有LIBERO回合的220步截止计分，保留原分母和matched100范围，不覆盖原结果 |

## 数字怎样追溯

从 CSV 中的模型、条件和运行编号，找到[实验说明](../docs/EXPERIMENTS_CN.md)与[实验日志](../docs/NOTES_CN.md)中的对应运行，再核对原始 JSON。公开权重的 revision 同时记录在 `reproduction.csv` 与 [dashboard/build.py](../dashboard/build.py) 的 `RUNS` 中。

重复同一批初始状态不等于增加独立样本；`official_pi0_summary.csv` 中 LeRobot 全涂黑一行合计了五次运行，比较时须遵守实验说明的配对口径。

重复同100初态的LeRobot全黑/双路冻结，原汇总仍保留执行总数与均值，但不再给合并Wilson区间；逐次100回合结果见新增匹配表。

## 重新生成

在仓库根目录执行，Python3.10+；第三步P1/P2 bootstrap需要NumPy，前两步仅标准库。无需GPU或仿真；分析环境见[快速开始](../README_CN.md#快速开始)：

```bash
python3 dashboard/build.py
python3 scripts/analysis/make_figures.py
python3 scripts/analysis/summarize_followup.py
```

依次生成看板数据、原有CSV/图件和P1/P2的CSV/图件，以及供网页摘要使用的[dashboard/followup.js](../dashboard/followup.js)，数字来自同一批记录。P1重采样保留同一状态的三轮与四条件，P2按固定任务内目标状态分层；不混用两者分母。

`trajectories_task4.json` 与 `trajectories_task7.json` 是轨迹图使用的精简 XY 数据（cm）。它们由 [export_trajectories.py](../scripts/analysis/export_trajectories.py) 从原始 NPZ 单独导出，需要 NumPy 与原始轨迹，不由上述三条命令重新生成。

P1/P2公开来源分别为[state_feedback](../dashboard/data/state_feedback/)和[replay_holdout](../dashboard/data/replay_holdout/)，哈希绑定逐运行/逐回合记录；原始完整NPZ不入Git，张量审计范围与记录缺口见各目录README。

协议补证见[95组来源与长度记录](../dashboard/data/protocol_audit/)。`budget_sensitivity.csv`的`source_episodes`是原运行回合数，`episodes`是有证据可重计的范围；`original_successes`仅对应这个范围，不能误作全运行结果。`successes_by_220`是已记录回合在220步内成功数；不重新推理或补跑。用`python scripts/analysis/summarize_protocol_audit.py`只读核查，`--write`经来源审查后重建此补充表。
