# 机器人策略到底有没有在看相机?

**在 MuJoCo 里复现六个开源机器人策略,再测每个策略对视觉的依赖程度。**

[![CI](https://github.com/chaoshengsc/robot-policy-sim-repro/actions/workflows/ci.yml/badge.svg)](https://github.com/chaoshengsc/robot-policy-sim-repro/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Dashboard](https://img.shields.io/badge/results-live%20dashboard-2563eb)](https://chaoshengsc.github.io/robot-policy-sim-repro/dashboard/?lang=zh)

[English](README.md) | 中文

<p align="center">
  <img src="media/zh/blackout_demo.gif" width="720" alt="同一个 LIBERO 任务的三次运行:π0.5 正常画面成功,π0.5 相机涂黑失败,π0 相机涂黑仍然成功">
  <br><sub>同一任务、同一初始状态。视频是仿真器里实际发生的情况;右边两次运行中,策略收到的是全黑图像。</sub>
</p>

- **复现。** ACT、OpenVLA、π0.5、Diffusion Policy 的成功率复现到基准的误差范围内;π0 和 SmolVLA 的公开权重没有(73% 对 97%,75% 对 90%)。
- **视觉依赖。** 把所有相机画面换成全黑后,π0.5、OpenVLA、SmolVLA 降到 0%,π0 仍有 56%。
- **原因。** π0 不用主视角相机,画面冻结也几乎不受影响,主要依赖机械臂状态输入。微调时把状态随机置零,能让它更依赖视觉。

全部在一台工作站上完成(RTX A5000 24 GB,Ubuntu 24.04,EGL 无头渲染),只用公开权重;所有改动都是包装脚本,不改上游源码。

**目录:** [复现结果](#1-复现结果) · [视觉依赖](#2-策略有没有在用相机) · [快速开始](#快速开始) · [仓库结构](#仓库结构) · [局限](#局限) · [致谢与许可证](#致谢与许可证)

## 1. 复现结果

![本机成功率 vs 基准](media/zh/reproduction.svg)

| 模型 | 任务 | 本机(500 回合) | 基准 | 是否复现 |
|---|---|---|---|---|
| ACT | ALOHA Transfer Cube | **83.2%** | 83.0%(Hugging Face 仓库) | ✅ |
| OpenVLA | LIBERO-Spatial | **86.2%** | 84.7 ± 0.9%(官方 README) | ✅ |
| π0.5 | LIBERO-Spatial | **98.0%** | 98.8%(OpenPI),97.0%(LeRobot) | ✅ |
| Diffusion Policy | PushT | **63.0%** | 65.4%(LeRobot 模型卡) | ✅ |
| SmolVLA | LIBERO-Spatial | 75.2% | 90%(论文) | ❌ |
| π0 | LIBERO-Spatial | 73.4% | 96.8%(OpenPI) | ❌ |

500 回合的 95% 置信区间约 ±3–4 个百分点。"复现"指两个区间有重叠。

<p align="center"><img src="media/act_transfer_cube_success.gif" width="320" alt="ACT 的一个成功回合"><br><sub>ACT · ALOHA Transfer Cube:右臂抓起方块交给左臂。</sub></p>

两个没复现的原因:

- **π0。** 基准数字是 OpenPI 自己训练的权重。这里用的 LeRobot 公开权重训练不足(维护者已确认),社区对同一权重的实测也是 73%。
- **SmolVLA。** 公开权重和论文的结构不同(expert 宽度 0.5、VLM 32 层,论文是 0.75、16 层)。社区对同一权重的实测约 82%;本机仍比它低 7 个百分点,原因没找到。batch size 和 `n_action_steps` 已排除。

把 π0 的 `n_action_steps` 从 5 改成 10、50,成功率是 76%、70%、68%(各 100 回合),差异在误差内。

各任务明细和回放在[看板](https://chaoshengsc.github.io/robot-policy-sim-repro/dashboard/?lang=zh)上;基准出处与排查过程见 [`docs/NOTES.md`](docs/NOTES.md)。

## 2. 策略有没有在用相机?

LIBERO 上的策略收到两路相机画面、机械臂状态和一句任务指令。下面每个实验只改其中一项。

![策略的输入,以及各实验改了哪一项](media/zh/inputs.svg)

本节所有数字都是 100 回合的成功率(10 个任务 × 10 个初始状态,各条件用同一个种子),95% 置信区间约 ±9 个百分点。

### 2.1 把所有相机涂黑

| 模型 | 正常 | 全涂黑 |
|---|---|---|
| π0.5 | 99% | 0% |
| OpenVLA | 81% | 0% |
| SmolVLA | 72% | 0% |
| **π0** | 76% | **56%** |

三个模型没有画面就完全不能动作;π0 看不见也能完成一半以上的任务,与 lerobot issue #3591 的报告一致。

### 2.2 是哪一路相机,什么样的扰动?

![各种扰动下的成功率](media/zh/perturbations.svg)

| 模型 | 正常 | 加高斯噪声 | 冻结首帧 | 只涂主视角 | 只涂腕部 | 全涂黑 |
|---|---|---|---|---|---|---|
| π0 | 76% | 79% | 71% | 78% | 59% | 56% |
| π0.5 | 99% | 99% | 0% | 51% | 0% | 0% |
| SmolVLA | 72% | 32% | 在跑 | 2% | 5% | 0% |

- **π0** 完全不用主视角相机(涂黑后 78%),也几乎不需要实时画面:整个回合只给它第一帧,只掉 5 个百分点。
- **π0.5** 对视觉是闭环的:加噪声没有影响,但画面冻结或腕部相机涂黑都会降到 0%。
- **SmolVLA** 在任何扰动下都崩溃,连轻微噪声也是,更像是对分布外输入敏感。

噪声是标准差 0.1 的高斯噪声,像素范围 [0, 1]。

### 2.3 看不见的 π0 是在背轨迹吗?

不是。评测时逐步记录了末端执行器位置,用动态时间规整(DTW)比较路线,消除了快慢差异。

![π0 有无相机输入时的末端路线](media/zh/trajectory.svg)

| 对比 | 路线差异 | 抓取点距离 |
|---|---|---|
| π0 正常 vs π0 正常重跑(噪声底线) | 2.12 cm | 1.51 cm |
| **π0 全涂黑 vs π0 正常** | **4.44 cm** | **5.03 cm** |
| π0.5 vs π0,都正常 | 3.28 cm | 2.65 cm |

看不见的 π0 走的路线和看得见时不同,差异约为噪声底线的两倍;它的抓取点也没有聚到同一个位置,所以不是在执行一套固定的"平均动作"。

更可能的解释在基准本身:LIBERO-Spatial 同一任务内,不同初始状态的抓取点只相差约 1.8 cm,和模型自身两次运行之间的噪声同一量级。抓偏 5 cm 的策略仍有约一半机会成功。

### 2.4 训练能让 π0 去看画面吗?

从公开的 π0 权重继续训练 3000 步(batch 16,只训动作专家,约为原训练量的 15%)。改动组训练时对 50% 的样本把 `observation.state` 置零。

| 模型 | 正常 | 全涂黑 |
|---|---|---|
| 原始 π0 | 76% | 56% |
| 继续微调,对照组 | 78% | 61% |
| 继续微调,状态置零 | 68% | **40%** |

全涂黑的成功率从 61% 降到 40%(z ≈ 3.0,p ≈ 0.003),说明模型更依赖视觉了。正常成功率从 78% 降到 68%,不显著(p ≈ 0.11)。第一次去掉状态时训练损失从 0.145 跳到 0.835,可见原来的 π0 对状态依赖很重。

1 万步的版本正在跑,结果出来后补在这里。

## 快速开始

```bash
export EMB_ROOT=/path/to/workdir      # 环境、缓存、权重、日志都放这里
# 按 docs/INSTALL.md 装好环境并下载权重后:
bash scripts/eval/run_act.sh          # ACT,500 回合,RTX A5000 上约 17 分钟
python3 scripts/analysis/summarize_eval.py act_cube_500
```

从原始评测文件重新生成本页的图和表(不需要 GPU,不需要装任何依赖):

```bash
python3 dashboard/build.py && python3 scripts/analysis/make_figures.py
```

| 文档 | 内容 |
|---|---|
| [`docs/INSTALL.md`](docs/INSTALL.md) | 三个 conda 环境、权重、分词器的逐步安装 |
| [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) | 安装和评测中遇到的每个问题:现象、原因、解决 |
| [`scripts/README.md`](scripts/README.md) | 每个结果对应哪个入口脚本和汇总脚本 |
| [`env/lock/`](env/lock/) | 从实际跑出结果的环境导出的完整包清单 |

## 仓库结构

```
scripts/eval/      评测入口;涂黑、扰动、轨迹记录的包装脚本
scripts/train/     π0 状态置零微调与全自动流水线
scripts/analysis/  指标、汇总、出图
scripts/checks/    GPU、EGL 无头渲染、视频解码自检
results/           结果表(CSV)与轨迹数据,由 dashboard/data 生成
dashboard/         结果看板,以及每次评测的原始 eval_info.json
media/             本页用的图与演示(中文版在 media/zh/)
docs/              安装、排查、复现笔记
env/               环境文件、pip 约束、导出的包清单
tests/             指标的单元测试,以及对已发布数字的一致性检查
viewer/            在本地用 MuJoCo 交互查看器回放策略轨迹
```

## 局限

- 只用了一个基准套件(LIBERO-Spatial)和一个种子。同一任务内场景变化很小,这本身就是 2.3 的发现之一。
- 视觉依赖实验每个条件 100 回合,10 个百分点以内的差异没有意义。
- π0 的公开权重训练不足,训练充分的 π0 表现可能不同。
- SmolVLA 与社区数字的差距原因未明。
- 2.4 的微调训练量小,且只训了动作专家。

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

权重:`lerobot/act_aloha_sim_transfer_cube_human`、`openvla/openvla-7b-finetuned-libero-spatial`、`HuggingFaceVLA/smolvla_libero`、`lerobot/pi05_libero_finetuned_v044`、`lerobot/pi0_libero_finetuned_v044`、`lerobot/diffusion_pusht`,具体 commit 见 [`results/reproduction.csv`](results/reproduction.csv)。各权重有自己的许可证。π0 的分词器来自受限仓库 `google/paligemma-3b-pt-224`,受 Gemma 条款约束,本仓库不包含。

论文:[ACT](https://arxiv.org/abs/2304.13705) · [Diffusion Policy](https://arxiv.org/abs/2303.04137) · [OpenVLA](https://arxiv.org/abs/2406.09246) · [LIBERO](https://arxiv.org/abs/2306.03310) · [SmolVLA](https://arxiv.org/abs/2506.01844) · [π0](https://arxiv.org/abs/2410.24164) · [π0.5](https://arxiv.org/abs/2504.16054)

## 引用

见 [`CITATION.cff`](CITATION.cff),或用 GitHub 页面上的 "Cite this repository" 按钮。
