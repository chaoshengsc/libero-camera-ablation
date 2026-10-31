# 脚本索引

[English](README.md) · [项目首页](../README_CN.md) · [文档导航](../docs/README_CN.md)

从要复现的结果选择入口。以下表格链接到源文件；带参数入口的用法以文件开头和运行时提示为准。相对路径按仓库根目录解释。

## 先准备什么

先完成[安装](../docs/INSTALL_CN.md)和[环境配置](../env/README_CN.md)，设置 `EMB_ROOT` 并准备相应权重。Shell 评测入口加载 [common.sh](common.sh)，再读取 `$EMB_ROOT/env.sh` 与本地权重路径。

评测包装器通过运行时替换函数实现干预，不修改 LeRobot / OpenVLA 源码。需要 GPU 或模型前向的入口与只处理已有数据的分析脚本分开列在下面。

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
- 底座 `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` 必须已在 Hugging Face 缓存中。

## 相机消融与官方 π0

| 实验 | 入口 | 结果与解释 |
|---|---|---|
| 四种模型全涂黑 | [run_blackout_all.sh](eval/run_blackout_all.sh) | [summarize_blackout.py](analysis/summarize_blackout.py) · [实验 1.1](../docs/EXPERIMENTS_CN.md#11-所有相机涂黑) |
| 加噪声、冻结首帧 | [run_perturbation.sh](eval/run_perturbation.sh) | [实验 1.2](../docs/EXPERIMENTS_CN.md#12-单路相机噪声冻结画面) |
| 末端轨迹、单路相机涂黑 | [run_trajectory_and_single_camera.sh](eval/run_trajectory_and_single_camera.sh) | [轨迹分析](analysis/analyze_trajectories.py) · [单路汇总](analysis/summarize_single_camera.py) |
| 官方 π0 对照、单路屏蔽、冻结与回放 | [run_official_pi0.sh](eval/run_official_pi0.sh) | [实验 1.5–1.6](../docs/EXPERIMENTS_CN.md#15-官方-π0-对照) |

官方 π0 的 OpenPI 路径需要独立环境和已启动的本机 [serve_pi0_libero.py](openpi/serve_pi0_libero.py) 服务。权重下载入口为 [download_checkpoint.py](openpi/download_checkpoint.py)，分阶段运行约定见入口文件和[实验日志](../docs/NOTES_CN.md)。它与 LeRobot 转换版不是同一条推理管线。

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

新结果接入：把评测输出中的 `eval_info.json` 放到 `dashboard/data/<run>/`，在 `dashboard/build.py` 注册对应运行，再依次执行下列命令。官方对照等专题汇总还需提供对应的配对/哈希记录，不能只填一个成功率。

```bash
python3 dashboard/build.py
python3 scripts/analysis/make_figures.py
```

两条命令在仓库根目录执行，分别更新看板数据和结果图表。[结果目录](../results/README_CN.md)列出产物，[CI](../.github/workflows/ci.yml)核对生成一致性。

## 自检、诊断与历史实验

- **环境自检：** [torch_check.py](checks/torch_check.py)、[egl_smoke.py](checks/egl_smoke.py)、[codec_check.py](checks/codec_check.py)，分别检查 GPU/torch、EGL 与视频解码。
- **π0 诊断：** [run_pi0_full.sh](eval/run_pi0_full.sh) 与 [run_pi0_action_steps.sh](eval/run_pi0_action_steps.sh)，对应历史冒烟、完整评测和动作块长度检查。
- **历史微调：** [run_statedrop_pipeline.sh](train/run_statedrop_pipeline.sh) 调用 [run_train.sh](train/run_train.sh)，由 [summarize_statedrop.py](analysis/summarize_statedrop.py) 汇总。结果与后续更正保留在[实验日志](../docs/NOTES_CN.md)，不作为 README 的主要发现。
