# 结果目录

[English](README.md) · [项目首页](../README_CN.md) · [文档导航](../docs/README_CN.md)

这里保存可重算的结果表；方法、比较范围与判读见[实验说明](../docs/EXPERIMENTS_CN.md)，原始评测在 [dashboard/data/](../dashboard/data/)。

## 按实验找结果

| 文件 | 内容 |
|---|---|
| [reproduction.csv](reproduction.csv) | 五个公开权重、基准与置信区间 |
| [blackout_per_task.csv](blackout_per_task.csv) | 四种模型全涂黑前后的逐任务成功次数 |
| [perturbations.csv](perturbations.csv) | 噪声、冻结、单路涂黑与重复运行 |
| [trajectory.csv](trajectory.csv) | 两次轨迹比较、DTW 与抓取点差异 |
| [single_camera_summary.csv](single_camera_summary.csv) | 500 回合单路相机汇总与配对统计 |
| [single_camera.csv](single_camera.csv) | 单路相机逐回合成功标记与首帧哈希 |
| [official_pi0_summary.csv](official_pi0_summary.csv) | 官方/OpenPI、LeRobot 与渲染对照 |
| [open_loop_replay.csv](open_loop_replay.csv) | 自回放、交叉回放与事后挑选偏差 |

## 数字怎样追溯

从 CSV 中的模型、条件和运行编号，找到[实验说明](../docs/EXPERIMENTS_CN.md)与[实验日志](../docs/NOTES_CN.md)中的对应运行，再核对原始 JSON。公开权重的 revision 同时记录在 `reproduction.csv` 与 [dashboard/build.py](../dashboard/build.py) 的 `RUNS` 中。

重复同一批初始状态不等于增加独立样本；`official_pi0_summary.csv` 中 LeRobot 全涂黑一行合计了五次运行，比较时须遵守实验说明的配对口径。

## 重新生成

在仓库根目录执行，Python 3.10+、仅标准库，无需 GPU：

```bash
python3 dashboard/build.py
python3 scripts/analysis/make_figures.py
```

第一步生成看板数据，第二步更新本目录的 CSV 与 `media/` 图件。

`trajectories_task4.json` 与 `trajectories_task7.json` 是轨迹图使用的精简 XY 数据（cm）。它们由 [export_trajectories.py](../scripts/analysis/export_trajectories.py) 从原始 NPZ 单独导出，需要 NumPy 与原始轨迹，不由上述两条命令重新生成。
