# 四个机器人策略在 LIBERO-Spatial 上的相机输入消融

**四个策略里有三个离开实时相机画面就无法完成任务;一个公开的 π0 权重在所有相机涂黑后仍有 54–56% 的成功率。**

[![CI](https://github.com/chaoshengsc/libero-camera-ablation/actions/workflows/ci.yml/badge.svg)](https://github.com/chaoshengsc/libero-camera-ablation/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Dashboard](https://img.shields.io/badge/results-live%20dashboard-2563eb)](https://chaoshengsc.github.io/libero-camera-ablation/dashboard/?lang=zh)

[English](README.md) | 中文

<p align="center">
  <img src="media/zh/blackout_demo.gif" width="720" alt="同一个 LIBERO 任务的三次运行:π0.5 正常画面成功,π0.5 相机涂黑失败,π0 相机涂黑仍然成功">
  <br><sub>同一任务、同一初始状态。视频是仿真器里实际发生的情况;右边两次运行中,策略收到的是全黑图像。</sub>
</p>

- **做了什么。** 对四个公开的 LIBERO 权重(π0、π0.5、OpenVLA、SmolVLA)改动相机输入:全涂黑、冻结在第一帧、加噪声、只去掉两路相机中的一路。机械臂状态和任务指令不变。
- **结果。** 相机全涂黑后,π0.5、OpenVLA、SmolVLA 降到 0%;画面冻结后,π0.5 和 SmolVLA 也降到 0%。LeRobot 的公开 π0 权重在全涂黑后从 76% 降到 56%,画面冻结后是 71%。
- **由此可知。** 在 LIBERO-Spatial 上,只看成功率看不出策略有没有在用相机。涂黑或冻结画面是一种成本很低的检查。
- **适用范围。** 一个套件、一个种子、每个条件 100 回合。这个 π0 权重训练不足,所以它的结果只说明这个权重,不代表所有 π0。

做消融之前,先把五个公开权重复现到了基准成功率的抽样误差范围内([第 2 节](#2-公开权重的复现))。全部在一台工作站上完成(RTX A5000 24 GB,Ubuntu 24.04,EGL 无头渲染),所有改动都是包装脚本,不改上游源码。本页的结果表由 CI 从 `dashboard/data/` 里的原始评测文件重新计算并核对。

**目录:** [相机消融](#1-相机消融) · [复现](#2-公开权重的复现) · [快速开始](#快速开始) · [仓库结构](#仓库结构) · [局限](#局限) · [致谢与许可证](#致谢与许可证)

## 1. 相机消融

LIBERO 上的策略收到两路相机画面、机械臂状态(末端位姿与夹爪开合)和一句任务指令。每个实验只改相机输入。

![策略的输入,以及各实验改了哪一项](media/zh/inputs.svg)

本节所有数字都是 100 回合的成功率(10 个任务 × 10 个初始状态,各条件用同一个种子)。两个条件要相差约 13 个百分点以上才有意义。

### 1.1 所有相机涂黑

| 模型 | 正常 | 全涂黑 |
|---|---|---|
| π0.5 | 99% | 0% |
| OpenVLA | 81% | 0% |
| SmolVLA | 83% | 0% |
| **π0** | 76% | **56%** |

三个模型没有画面就完全不能动作。π0 仍有 56% 的回合成功:七个任务上 10 次成功 6 到 9 次,另外三个任务上 0 或 1 次。另一次独立运行是 54%,lerobot issue #3591 对同一个权重报告的是约 60%。

### 1.2 单路相机、噪声、冻结画面

![各种扰动下的成功率](media/zh/perturbations.svg)

| 模型 | 正常 | 加高斯噪声 | 冻结首帧 | 只涂主视角 | 只涂腕部 | 全涂黑 |
|---|---|---|---|---|---|---|
| π0 | 76% | 79% | 71% | 78% | 59% | 56% |
| π0.5 | 99% | 99% | 0% | 51% | 0% | 0% |
| SmolVLA | 83% | 78% | 0% | 33% | 4% | 0% |

- **π0.5 和 SmolVLA 需要实时画面。** 冻结的第一帧是真实的、分布内的画面,但两个模型都降到 0%。加噪声对两者的影响都在抽样误差之内。
- **π0 基本不需要。** 整个回合只给第一帧,它仍有 71%,与正常时的差别在误差之内。它对主视角相机测不出依赖(涂黑后 78%)。只涂腕部相机(59%)和两路都涂(56%)损失差不多,说明 π0 确实用到了腕部画面。
- **对三个模型来说,腕部相机都比主视角更重要。**

OpenVLA 只接收主视角画面和指令,所以对它只有"全涂黑"这一个条件。

### 1.3 看不见的 π0 在成功的任务上走的是同一条路线

逐步记录了末端执行器的位置,用动态时间规整比较路线(消除速度差异)。

![π0 有无相机输入时的末端路线](media/zh/trajectory.svg)

| 比较 | 路线差异 | 抓取点差异 |
|---|---|---|
| 看不见的 π0 对看得见的 π0,取前者至少成功一半的七个任务 | 2.8 cm | 2.4 cm |
| π0.5 对 π0,都看得见,同样七个任务 | 2.9 cm | 2.6 cm |
| 看得见的 π0 对它自己的重跑(任务 4–9) | 3.4 cm | 2.4 cm |
| 看不见的 π0 对看得见的 π0,取前者失败的三个任务 | 6 到 11 cm | |

在能完成的任务上,看不见的 π0 与看得见的 π0 之间的差别,和两次正常运行之间的差别一样大。在失败的任务上,它走到了别处。

这不能说明看不见的 π0 是不是在重复记住的动作。这种比较分不出"跟着碗走"的策略和"每个任务重复一套动作"的策略,而同一任务的不同初始状态之间碗的位置变化有多大,这里没有测。各任务的数字见 [`results/trajectory.csv`](results/trajectory.csv) 和[看板](https://chaoshengsc.github.io/libero-camera-ablation/dashboard/?lang=zh)。

### 关于这些数字

- **π0 权重。** `lerobot/pi0_libero_finetuned_v044` 500 回合的正常成功率是 73.4%。OpenPI 旧版 README 给出过自家 π0 微调结果 96.8%,但那个权重没有发布,所以没有官方的 π0 LIBERO 权重可以对照。LeRobot 维护者说过公开的这个权重训练不足(lerobot issue #2114)。
- **"正常"一列。** 取自各模型 500 回合评测里每个任务的前 10 回合,它们与消融实验用的是同一批初始状态。
- **置信区间。** 单个数字的 95% 置信区间最宽约 ±10 个百分点。同一任务的回合之间相关,所以这些区间偏乐观。
- **噪声。** 高斯噪声,标准差 0.1,像素范围 [0, 1]。
- **相关工作。** [LIBERO-PRO](https://arxiv.org/abs/2510.03827) 和 [LIBERO-Plus](https://arxiv.org/abs/2510.13626) 用范围大得多的扰动研究了 LIBERO 策略的鲁棒性。

## 2. 公开权重的复现

![本仓库成功率 vs 基准](media/zh/reproduction.svg)

| 模型 | 任务 | 本仓库(500 回合) | 基准 | 是否复现 |
|---|---|---|---|---|
| ACT | ALOHA Transfer Cube | **83.2%** | 83.0%(Hugging Face 仓库) | ✅ |
| OpenVLA | LIBERO-Spatial | **86.2%** | 84.7 ± 0.9%(官方 README) | ✅ |
| SmolVLA | LIBERO-Spatial | **85.4%** | 90%(论文,100 回合) | ✅ |
| π0.5 | LIBERO-Spatial | **98.0%** | 98.8%(OpenPI),97.0%(LeRobot) | ✅ |
| Diffusion Policy | PushT(2D,非 MuJoCo) | **63.0%** | 65.4%(LeRobot 模型卡) | ✅ |

500 回合的 95% 置信区间为 ±1–4 个百分点。"复现"指两个区间有重叠。SmolVLA 是 `lerobot/smolvla_libero`,评测时 `n_action_steps=10`,与第 1 节是同一个权重。它只在 LIBERO-Spatial 上训练,论文则在四个 LIBERO 套件上训练;论文的 100 回合对应的基准区间约为 ±6 个百分点。

<p align="center"><img src="media/act_transfer_cube_success.gif" width="320" alt="ACT 的一个成功回合"><br><sub>ACT · ALOHA Transfer Cube:右臂抓起方块交给左臂。</sub></p>

各任务明细在[看板](https://chaoshengsc.github.io/libero-camera-ablation/dashboard/?lang=zh)上。回放视频体积大,没有发布;本地有视频文件时看板可以播放。基准出处与完整实验记录见 [`docs/NOTES_CN.md`](docs/NOTES_CN.md)。

## 快速开始

```bash
export EMB_ROOT=/path/to/workdir      # 环境、缓存、权重、日志都放这里
# 按 docs/INSTALL_CN.md 装好环境并下载权重后:
bash scripts/eval/run_act.sh          # ACT,500 回合,RTX A5000 上约 17 分钟
python3 scripts/analysis/summarize_eval.py act_cube_500
bash scripts/eval/run_blackout_all.sh  # 四个 LIBERO 模型相机全涂黑,各 100 回合
python3 scripts/analysis/summarize_blackout.py
```

从 `dashboard/data/` 里的评测文件重新生成本页的图和表(不需要 GPU,不需要装任何依赖):

```bash
python3 dashboard/build.py && python3 scripts/analysis/make_figures.py
```

| 文档 | 内容 |
|---|---|
| [`docs/INSTALL_CN.md`](docs/INSTALL_CN.md) | 三个 conda 环境、权重、分词器的逐步安装 |
| [`docs/TROUBLESHOOTING_CN.md`](docs/TROUBLESHOOTING_CN.md) | 安装和评测中遇到的每个问题:现象、原因、解决 |
| [`scripts/README_CN.md`](scripts/README_CN.md) | 每个结果对应哪个入口脚本和汇总脚本 |
| [`env/lock/`](env/lock/) | 从实际跑出结果的环境导出的完整包清单 |

## 仓库结构

```
scripts/eval/      评测入口;涂黑、扰动、轨迹记录的包装脚本
scripts/train/     π0 微调脚本,对应 docs/NOTES_CN.md 里记录的一个实验(不属于上面的结果)
scripts/analysis/  指标、汇总、出图
scripts/checks/    GPU、EGL 无头渲染、视频解码自检
results/           由 dashboard/data 生成的结果表(CSV),以及 1.3 节画图用的轨迹
dashboard/         结果看板,以及每次评测的原始 eval_info.json
media/             本页用的图与演示(中文版在 media/zh/)
docs/              安装、排查、复现笔记
env/               环境文件、pip 约束、导出的包清单
tests/             指标的单元测试、已发布数字的一致性检查、入口脚本的回归测试
viewer/            在本地用 MuJoCo 交互查看器回放策略轨迹
```

## 局限

- 只用了一个基准套件(LIBERO-Spatial)和一个种子。
- 消融实验每个条件 100 回合,约 13 个百分点以内的差异没有意义。
- π0 的公开权重训练不足,训练充分的 π0 表现可能不同。
- 同一任务的不同初始状态之间场景变化有多大,这里没有测,所以本仓库不能说明这个基准本身需要多少视觉。
- Diffusion Policy 评测的是 PushT(2D 物理),不在 MuJoCo 里。

## 致谢与许可证

本仓库不包含任何模型权重,也不包含上游源码。它建立在这些项目之上:

| 项目 | 用途 | 许可证 |
|---|---|---|
| [LeRobot](https://github.com/huggingface/lerobot) v0.6.1 | ACT、Diffusion Policy、SmolVLA、π0、π0.5 的评测与 π0 微调 | Apache-2.0 |
| [OpenVLA](https://github.com/openvla/openvla) | OpenVLA 评测 | MIT |
| [OpenPI](https://github.com/Physical-Intelligence/openpi) | π0、π0.5 的基准数字 | Apache-2.0 |
| [LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO) | 基准 | MIT |
| [Diffusion Policy](https://github.com/real-stanford/diffusion_policy)、[ACT](https://github.com/tonyzhaozh/act) | 原始方法 | MIT |
| [MuJoCo](https://github.com/google-deepmind/mujoco)、[gym-aloha](https://github.com/huggingface/gym-aloha)、[gym-pusht](https://github.com/huggingface/gym-pusht) | 仿真 | Apache-2.0 |

权重:`lerobot/act_aloha_sim_transfer_cube_human`、`openvla/openvla-7b-finetuned-libero-spatial`、`lerobot/smolvla_libero`、`lerobot/pi05_libero_finetuned_v044`、`lerobot/pi0_libero_finetuned_v044`、`lerobot/diffusion_pusht`,具体 commit 见 [`results/reproduction.csv`](results/reproduction.csv) 和 [`docs/NOTES_CN.md`](docs/NOTES_CN.md)。各权重有自己的许可证。π0 的分词器来自受限仓库 `google/paligemma-3b-pt-224`,受 Gemma 条款约束,本仓库不包含。

论文:[ACT](https://arxiv.org/abs/2304.13705) · [Diffusion Policy](https://arxiv.org/abs/2303.04137) · [OpenVLA](https://arxiv.org/abs/2406.09246) · [LIBERO](https://arxiv.org/abs/2306.03310) · [SmolVLA](https://arxiv.org/abs/2506.01844) · [π0](https://arxiv.org/abs/2410.24164) · [π0.5](https://arxiv.org/abs/2504.16054)

## 引用

见 [`CITATION.cff`](CITATION.cff),或用 GitHub 页面上的 "Cite this repository" 按钮。
