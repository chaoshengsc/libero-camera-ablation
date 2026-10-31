<div align="center">

# Do robot policies actually use their cameras?

Camera ablations of four robot policies on LIBERO-Spatial

[![CI](https://github.com/chaoshengsc/libero-camera-ablation/actions/workflows/ci.yml/badge.svg)](https://github.com/chaoshengsc/libero-camera-ablation/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/chaoshengsc/libero-camera-ablation?color=2563eb)](https://github.com/chaoshengsc/libero-camera-ablation/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

[English](README.md) · **中文**

[主要发现](#1-相机消融) · [复现结果](#2-公开权重的复现) · [快速开始](#快速开始) · [数据](results/README_CN.md) · [文档导航](docs/README_CN.md)

</div>

**机器人在仿真里完成了任务，是否就说明它在用相机？** 我们复现五个公开权重，并对 π0、π0.5、OpenVLA、SmolVLA 做相机输入消融，比较它们在 LIBERO-Spatial 上对画面的依赖。

**相机全涂黑后，三种模型成功率为 0%；LeRobot π0 v044 仍有 53–56%，官方 π0 在 OpenPI 中为 0/100。**

<p align="center">
  <img src="media/zh/blackout_demo.gif" width="720" height="300" alt="同一个 LIBERO 任务：π0.5 正常成功、相机涂黑失败，LeRobot π0 涂黑仍成功">
  <br><sub>同一任务、同一初始状态。右边两次运行中，模型收到的是全黑图像；视频展示仿真器里的实际动作。</sub>
</p>

| 你想做什么 | 从这里进入 |
|---|---|
| 看结论 | [主要发现](#1-相机消融) → [完整实验与图表](docs/EXPERIMENTS_CN.md) |
| 复现实验 | [安装](docs/INSTALL_CN.md) → [脚本索引](scripts/README_CN.md) → [排错](docs/TROUBLESHOOTING_CN.md) |
| 核对数字 | [结果表](results/README_CN.md) → [原始评测](dashboard/data/) → [实验日志与更正](docs/NOTES_CN.md) |

[文档导航](docs/README_CN.md) · [交互结果页](https://chaoshengsc.github.io/libero-camera-ablation/dashboard/?lang=zh) · [仓库结构](#仓库结构) · [局限](#局限)

## 1. 相机消融

### 所有相机涂黑

| 模型 | 正常画面 | 所有相机涂黑 |
|---|---|---|
| π0.5 | 99% | 0% |
| OpenVLA | 81% | 0% |
| SmolVLA | 83% | 0% |
| **π0 · LeRobot v044** | 76% | **56%** |

表中是各 100 回合的一组结果；正常条件取 500 回合评测中每任务的前 10 回合。前三个模型全涂黑后各重跑一次仍为 0%。π0 全涂黑五次为 **53–56%**，五次使用同一批 100 个初始状态，不能当成 500 个独立状态。

<a id="15-官方-π0-对照"></a>

### 官方 π0 对照

![官方 π0 与 LeRobot π0 的相机消融对照](media/zh/official_pi0.svg)

官方 π0 在 OpenPI 中正常为 **96.4%**，LeRobot π0 v044 在 LeRobot 中为 **72.0%**（各 500 回合）；相机全涂黑后，前者为 **0/100**，后者五次为 **53–56%**。

**看不见仍能成功的现象只在这里测试的 LeRobot π0 权重及其管线上出现。** 两边同时改变了权重与推理管线，差别不能单独归因到权重；渲染分辨率已通过 360 渲染复测排除。

其他检查补全了这幅图景：

- **实时画面。** π0.5 和 SmolVLA 冻结首帧后，两次运行都为 0%；只去掉腕部相机时，π0.5 从 98.4% 降到 4.6%（各 500 回合）。
- **固定动作回放。** 交叉回放合计 **348/873 = 39.9%**，自回放为 95/97。事后挑选每任务最好动作得到的 77.8% 有选择偏差，不能当作无偏基线，也不能据此确定 LeRobot π0 的机制。

完整设计、重复运行、逐任务结果与统计口径见[实验说明](docs/EXPERIMENTS_CN.md)；原始记录与更正见[实验日志](docs/NOTES_CN.md)。

## 2. 公开权重的复现

| 模型 | 任务 | 本仓库（500 回合） | 基准 | 是否复现 |
|---|---|---|---|---|
| ACT | ALOHA Transfer Cube | **83.2%** | 83.0%（Hugging Face 仓库） | ✅ |
| OpenVLA | LIBERO-Spatial | **86.2%** | 84.7 ± 0.9%（官方 README） | ✅ |
| SmolVLA | LIBERO-Spatial | **85.4%** | 90%（论文，100 回合） | ✅ |
| π0.5 | LIBERO-Spatial | **98.0%** | 98.8%（OpenPI），97.0%（LeRobot） | ✅ |
| Diffusion Policy | PushT（2D，非 MuJoCo） | **63.0%** | 65.4%（LeRobot 模型卡） | ✅ |

“复现”指本仓库与基准的两个 95% 置信区间有重叠。各模型评测 500 回合，对应区间约 ±1–4 个百分点。

SmolVLA 使用 `lerobot/smolvla_libero`，`n_action_steps=10`，只在 LIBERO-Spatial 上训练；论文基准来自四套件训练，100 回合的区间约 ±6 个百分点。完整出处见[复现说明](docs/EXPERIMENTS_CN.md#2-公开权重的复现)。

## 快速开始

本仓库的结果在 Ubuntu 24.04、RTX A5000 24 GB 上取得。环境版本与安装步骤见[安装指南](docs/INSTALL_CN.md)；权重来源与 revision 见[结果目录](results/README_CN.md)。

先配置好环境、`EMB_ROOT` 与权重，再从仓库根目录运行一个 ACT 示例：

```bash
bash scripts/eval/run_act.sh
python3 scripts/analysis/summarize_eval.py act_cube_500
```

第一条执行 500 回合 GPU 评测，第二条汇总已有输出。环境或权重未就绪时，回到[安装](docs/INSTALL_CN.md)与[排错](docs/TROUBLESHOOTING_CN.md)；其他模型和消融的入口见[脚本索引](scripts/README_CN.md)。

<details>
<summary>无需 GPU：从已有数据重算表格和图件</summary>

在仓库根目录使用 Python 3.10+ 执行，仅依赖标准库：

```bash
python3 dashboard/build.py
python3 scripts/analysis/make_figures.py
```

第一步从原始记录生成看板数据，第二步生成 CSV 与中英文 SVG。完成后可查看 [results/](results/README_CN.md) 和 [media/](media/)；缺少原始文件时应先排查数据来源。

</details>

## 仓库结构

```text
libero-camera-ablation/
├── README.md / README_CN.md   项目概览与主要结论
├── docs/                     完整实验、安装、排错与历史记录
├── scripts/                  评测、干预、汇总与出图
├── env/                      环境配置、版本约束与导出清单
├── results/                  可重算的结果表与轨迹数据
├── media/                    图表与演示；中文图在 zh/
├── dashboard/                交互结果页及数据生成入口
│   └── data/                 原始评测与诊断记录
├── viewer/                   本地 MuJoCo 轨迹查看器
├── tests/                    指标与公开数字的一致性检查
└── .github/                  CI 与问题模板
```

[文档地图](docs/README_CN.md) · [执行入口](scripts/README_CN.md) · [结果目录](results/README_CN.md) · [环境目录](env/README_CN.md)

## 局限

- 只用了一个基准套件（LIBERO-Spatial）和一个种子。
- [实验 1.1–1.3](docs/EXPERIMENTS_CN.md#11-所有相机涂黑)的消融每次运行 100 回合，约 13 个百分点以内的差异没有意义（[单路相机实验](docs/EXPERIMENTS_CN.md#14-只去掉腕部相机500-回合)为 500 回合）；对 π0，同一个条件重复运行最多相差 18 个百分点。
- π0 的消融结论来自 LeRobot v044 权重；官方 π0 只在 OpenPI 原版管线下测过，两边的管线不同（渲染分辨率已用 360 复测排除），差别不能单独归因到权重。官方 π0 的消融条件各只跑了一次 100 回合。
- [官方对照与回放](docs/EXPERIMENTS_CN.md#15-官方-π0-对照)已测量每任务 50 个初始状态中的物体位置变化，最大坐标跨度为 3–9 cm；固定动作交叉回放合计成功率为 39.9%。这只描述所测状态与动作序列，不能确定整个基准需要多少视觉，也不能确定 LeRobot π0 无视觉成功的机制。
- Diffusion Policy 评测的是 PushT（2D 物理），不在 MuJoCo 里。

## 致谢与许可证

代码使用 [MIT 许可证](LICENSE)。模型、分词器与上游项目各自的许可证仍适用；权重和分词器不包含在仓库里。

<details>
<summary>上游项目、权重来源与论文</summary>

本仓库不包含任何模型权重，也不包含上游源码。它建立在这些项目之上：

| 项目 | 用途 | 许可证 |
|---|---|---|
| [LeRobot](https://github.com/huggingface/lerobot) v0.6.1 | ACT、Diffusion Policy、SmolVLA、π0、π0.5 的评测与 π0 微调 | Apache-2.0 |
| [OpenVLA](https://github.com/openvla/openvla) | OpenVLA 评测 | MIT |
| [OpenPI](https://github.com/Physical-Intelligence/openpi) | π0、π0.5 的基准数字 | Apache-2.0 |
| [LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO) | 基准 | MIT |
| [Diffusion Policy](https://github.com/real-stanford/diffusion_policy)、[ACT](https://github.com/tonyzhaozh/act) | 原始方法 | MIT |
| [MuJoCo](https://github.com/google-deepmind/mujoco)、[gym-aloha](https://github.com/huggingface/gym-aloha)、[gym-pusht](https://github.com/huggingface/gym-pusht) | 仿真 | Apache-2.0 |

权重：`lerobot/act_aloha_sim_transfer_cube_human`、`openvla/openvla-7b-finetuned-libero-spatial`、`lerobot/smolvla_libero`、`lerobot/pi05_libero_finetuned_v044`、`lerobot/pi0_libero_finetuned_v044`、`lerobot/diffusion_pusht`，具体 commit 见 [`results/reproduction.csv`](results/reproduction.csv) 和 [`docs/NOTES_CN.md`](docs/NOTES_CN.md)。各权重有自己的许可证。π0 的分词器来自受限仓库 `google/paligemma-3b-pt-224`，受 Gemma 条款约束，本仓库不包含。

论文：[ACT](https://arxiv.org/abs/2304.13705) · [Diffusion Policy](https://arxiv.org/abs/2303.04137) · [OpenVLA](https://arxiv.org/abs/2406.09246) · [LIBERO](https://arxiv.org/abs/2306.03310) · [SmolVLA](https://arxiv.org/abs/2506.01844) · [π0](https://arxiv.org/abs/2410.24164) · [π0.5](https://arxiv.org/abs/2504.16054)

</details>

## 引用

如果用到了这里的结果或脚本，请引用：

```bibtex
@software{shengchao2026liberocameraablation,
  author  = {ShengChao},
  title   = {libero-camera-ablation: Camera-input ablations of four robot policies on LIBERO-Spatial},
  year    = {2026},
  version = {1.4.0},
  url     = {https://github.com/chaoshengsc/libero-camera-ablation}
}
```

同样的条目也在 [`CITATION.cff`](CITATION.cff) 里，GitHub 页面上的 “Cite this repository” 按钮读的就是它。
