# 脚本索引

所有入口都先 `source scripts/common.sh`:它加载 `$EMB_ROOT/env.sh`,并定义各公开权重的本地路径(`CK_PI0` 等)。
包装脚本(`eval_*.py`、`train_statedrop.py`、`migrate_tuplefix.py`)都是运行时替换函数,不改 LeRobot / OpenVLA 源码。

| 结果 | 入口 | 汇总 |
|---|---|---|
| ACT 500 回合 | `eval/run_act.sh` | `analysis/summarize_eval.py` |
| Diffusion Policy · PushT 500 回合 | `eval/run_dp_pusht.sh` | `analysis/summarize_eval.py` |
| OpenVLA · LIBERO-Spatial | `eval/run_ovla.sh <run> 50` | `analysis/ovla_to_json.py` |
| SmolVLA / π0 / π0.5 · LIBERO-Spatial | `eval/run_libero.sh <run> 50 <权重目录> 1 [...]` | `analysis/summarize_eval.py` |
| π0 冒烟测试 + 完整评测 | `eval/run_pi0_full.sh` | |
| π0 的 `n_action_steps` | `eval/run_pi0_action_steps.sh` | `analysis/summarize_eval.py` |
| 四个模型全涂黑 | `eval/run_blackout_all.sh` | `analysis/summarize_blackout.py` |
| 录像逐帧比较 | | `analysis/compare_videos.py` |
| 末端轨迹、只涂黑一路相机 | `eval/run_trajectory_and_single_camera.sh` | `analysis/analyze_trajectories.py`、`analysis/summarize_single_camera.py` |
| 温和扰动:加噪声、冻结画面 | `eval/run_perturbation.sh` | `dashboard/build.py` |
| 状态置零继续微调 | `train/run_statedrop_pipeline.sh`(内部调 `train/run_train.sh`) | `analysis/summarize_statedrop.py` |
| 轨迹图的数据 | | `analysis/export_trajectories.py` |
| README 的图与 `results/*.csv` | | `analysis/make_figures.py` |

`eval/run_libero.sh` 的 `WRAP` 开关:

| `WRAP` | 实际运行 | 额外环境变量 |
|---|---|---|
| `none`(默认) | `lerobot-eval` | |
| `blackout` | `eval/eval_blackout.py` | `BLACKOUT=all\|agent\|wrist` |
| `probe` | `eval/eval_probe.py`,轨迹存到 `<输出目录>/traj.npz` | `BLACKOUT=none\|all\|agent\|wrist\|noise\|freeze` |

`checks/` 下三个脚本用于装完环境后的自检:GPU 与 torch、EGL 无头渲染、视频解码。

`analysis/metrics.py` 是各分析脚本共用的指标(置信区间、两比例 z 检验、DTW、抓取点),有单元测试(`tests/`)。
