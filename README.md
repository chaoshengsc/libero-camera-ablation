# Camera-input ablations of four robot policies on LIBERO-Spatial

**Three of the four policies fail without a live camera image. One public π0 checkpoint still succeeds 53–56% of the time with every camera blacked out.**

[![CI](https://github.com/chaoshengsc/libero-camera-ablation/actions/workflows/ci.yml/badge.svg)](https://github.com/chaoshengsc/libero-camera-ablation/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Dashboard](https://img.shields.io/badge/results-live%20dashboard-2563eb)](https://chaoshengsc.github.io/libero-camera-ablation/dashboard/)

English | [中文](README_CN.md)

<p align="center">
  <img src="media/blackout_demo.gif" width="720" alt="Three rollouts of the same LIBERO task: pi0.5 with cameras succeeds, pi0.5 with black camera input fails, pi0 with black camera input still succeeds">
  <br><sub>Same task, same initial state. The videos show what happened in the simulator; in the two right-hand runs the policy itself received black images.</sub>
</p>

- **What was done.** Four public LIBERO checkpoints (π0, π0.5, OpenVLA, SmolVLA) were evaluated with the camera input blacked out, frozen at the first frame, noised, or with one of the two cameras removed. Robot state and instruction were left unchanged.
- **Result.** π0.5, OpenVLA and SmolVLA drop to 0% with black cameras, and π0.5 and SmolVLA also drop to 0% when the image is frozen. LeRobot's public π0 checkpoint scores 71–76% normally, 53–56% with black cameras (five runs each), and 71% and 80% in two runs with a frozen image.
- **What follows from it.** On LIBERO-Spatial, a success rate alone does not show whether a policy uses its cameras. Blacking out or freezing the image is a cheap way to check.
- **Scope.** One suite, one seed, 100 episodes per run; the single-camera, noise and frozen-image conditions were each run twice. The π0 checkpoint is under-trained, so its result describes this checkpoint and not π0 in general.

Before the ablations, five public checkpoints were reproduced to within sampling error of their reference success rates ([section 2](#2-reproduction-of-the-public-checkpoints)). Everything runs on one workstation (RTX A5000 24 GB, Ubuntu 24.04, headless EGL rendering), with wrapper scripts that leave upstream source untouched. CI recomputes the result tables on this page from the raw evaluation files in `dashboard/data/`.

**Contents:** [Camera ablations](#1-camera-ablations) · [Reproduction](#2-reproduction-of-the-public-checkpoints) · [Quick start](#quick-start) · [Layout](#repository-layout) · [Limitations](#limitations) · [Acknowledgements](#acknowledgements-and-licenses)

## 1. Camera ablations

A LIBERO policy receives two camera images, the robot state (end-effector pose and gripper opening) and a language instruction. Each experiment changes only the camera input.

![What the policy receives and what each experiment changes](media/inputs.svg)

Every number in this section is a success rate over 100 episodes (10 tasks × 10 initial states, same seed for every condition). Sampling error alone means two conditions have to differ by about 13 points. For π0 the bar is higher: the same condition run twice differed by up to 18 points (section 1.2).

### 1.1 All cameras black

| Model | Normal | All cameras black |
|---|---|---|
| π0.5 | 99% | 0% |
| OpenVLA | 81% | 0% |
| SmolVLA | 83% | 0% |
| **π0** | 76% | **56%** |

Three models cannot act without images. π0 succeeds in 56% of episodes: 6 to 9 out of 10 on seven tasks, and 0 or 1 out of 10 on the other three. Four more runs gave 54%, 56%, 54% and 53%, and lerobot issue #3591 reports about 60% for the same checkpoint.

### 1.2 One camera, noise, frozen image

![Success rate under each perturbation](media/perturbations.svg)

Success rate (%) in two runs of 100 episodes each, first run / second run. The second run repeats the same scripts with the same seed.

| Model | Normal | Gaussian noise | Frozen first frame | Agent-view black | Wrist black | All black |
|---|---|---|---|---|---|---|
| π0 | 76 / 72 | 79 / 67 | 71 / 80 | 78 / 68 | 59 / 77 | 56 / 56 |
| π0.5 | 99 / 98 | 99 / 97 | 0 / 0 | 51 / 57 | 0 / 0 | 0 / 0 |
| SmolVLA | 83 / – | 78 / 73 | 0 / 0 | 33 / 31 | 4 / 4 | 0 / 0 |

- **π0.5 and SmolVLA need a live image.** A frozen first frame is a real, in-distribution image, and it takes both to 0% in both runs. Noise changes neither beyond sampling error.
- **Only blacking out both cameras changes π0 reliably.** That costs about 20 points in every run. With noise, a frozen first frame, or one camera black, its two runs differ by 9 to 18 points and all land between 59% and 80%, around its normal 71–76%. These runs cannot show that π0 depends on either single camera. The first run alone suggested a wrist-camera dependence (59%); the second run (77%) did not repeat it.
- **For π0.5 and SmolVLA the wrist camera matters more than the agent view**, in both runs.

OpenVLA takes only the agent-view image and the instruction, so only the all-black condition applies to it.

### 1.3 Where blind π0 succeeds, it follows the sighted path

The end-effector position was logged at every step, and paths were compared with dynamic time warping, which removes speed differences.

![End-effector paths of pi0 with and without camera input](media/trajectory.svg)

| Comparison | Path difference | Grasp-point difference |
|---|---|---|
| Blind π0 vs. sighted π0, on the tasks blind π0 solves at least half the time | 2.8 / 3.2 cm | 2.4 / 2.2 cm |
| π0.5 vs. π0, both sighted, same tasks | 2.9 / 3.0 cm | 2.6 / 2.5 cm |
| Sighted π0 vs. its own re-run | 3.4 / 3.3 cm | 2.4 / 2.4 cm |
| Blind π0 vs. sighted π0, on task 7, where blind π0 never succeeds | 10.9 / 10.3 cm | 24.1 / 23.7 cm |

Each cell gives the first and the second run of the whole comparison. Blind π0 solves seven tasks at least half the time in the first run (0–4, 6, 8) and six in the second (0–4, 6).

On the tasks it solves, blind π0 is as close to sighted π0 as two sighted runs are to each other, in both runs. On task 7 it goes somewhere else in both runs; two sighted runs differ by 2.6 and 2.2 cm there. Task 9, where blind π0 succeeds 0 and 1 times out of 10, points the same way but less clearly: the path differs by 7.8 and 4.9 cm, against 3.3 and 3.6 cm between sighted runs. Task 5 (3 and 4 successes) is inconclusive: 6.0 and 6.6 cm, against 6.6 and 4.7 cm between sighted runs.

The re-run row leaves out tasks where the two sighted runs are still almost identical, because they use the same seed and had not yet diverged, so they say nothing about noise. These are tasks 0–3 in the first run and task 0 in the second.

This does not show whether blind π0 replays a memorised motion. The comparison cannot separate a policy that tracks the bowl from one that repeats one motion per task, and how much the bowl position varies between initial states was not measured here. Per-task numbers are in [`results/trajectory.csv`](results/trajectory.csv) and on the [dashboard](https://chaoshengsc.github.io/libero-camera-ablation/dashboard/).

### Notes on these numbers

- **π0 checkpoint.** `lerobot/pi0_libero_finetuned_v044` scores 73.4% over 500 normal episodes. An earlier OpenPI README gave 96.8% for its own π0 fine-tuning run, but that checkpoint was never released, so there is no official π0 LIBERO checkpoint to compare against. A LeRobot maintainer has said the public one is under-trained (lerobot issue #2114).
- **Normal column.** The first number is the first 10 episodes per task of each model's 500-episode run, which use the same initial states as the ablation runs. The second is a separate 100-episode run; SmolVLA has none. π0's five normal runs gave 76%, 73%, 76%, 72% and 71%.
- **Confidence intervals.** The 95% interval of a single number is up to ±10 points. Episodes of one task are correlated, which makes these intervals optimistic.
- **Run-to-run variation.** Runs with the same seed are not identical. π0.5 and SmolVLA repeat within 6 points; π0 differs by up to 18 points on the same condition.
- **Noise.** Gaussian, standard deviation 0.1, on pixels in [0, 1].
- **Related work.** [LIBERO-PRO](https://arxiv.org/abs/2510.03827) and [LIBERO-Plus](https://arxiv.org/abs/2510.13626) study the robustness of LIBERO policies under a much wider set of perturbations.

## 2. Reproduction of the public checkpoints

![Success rate in this repo vs. reference](media/reproduction.svg)

| Model | Task | This repo (500 episodes) | Reference | Reproduced |
|---|---|---|---|---|
| ACT | ALOHA Transfer Cube | **83.2%** | 83.0% (Hugging Face repo) | ✅ |
| OpenVLA | LIBERO-Spatial | **86.2%** | 84.7 ± 0.9% (official README) | ✅ |
| SmolVLA | LIBERO-Spatial | **85.4%** | 90% (paper, 100 episodes) | ✅ |
| π0.5 | LIBERO-Spatial | **98.0%** | 98.8% (OpenPI), 97.0% (LeRobot) | ✅ |
| Diffusion Policy | PushT (2-D, not MuJoCo) | **63.0%** | 65.4% (LeRobot model card) | ✅ |

The 95% confidence interval at 500 episodes is ±1–4 points. "Reproduced" means the two intervals overlap. SmolVLA is `lerobot/smolvla_libero` with `n_action_steps=10`, the same checkpoint as in section 1. It was trained on LIBERO-Spatial only, while the paper trains on all four LIBERO suites, and the paper's 100 episodes give a reference interval of about ±6 points.

<p align="center"><img src="media/act_transfer_cube_success.gif" width="320" alt="A successful ACT episode"><br><sub>ACT on ALOHA Transfer Cube: the right arm picks up the cube and hands it to the left arm.</sub></p>

Per-task results are on the [dashboard](https://chaoshengsc.github.io/libero-camera-ablation/dashboard/). Replay videos are too large to publish; the dashboard plays them when the files are present locally. Sources of the reference numbers and the full experiment log are in [`docs/NOTES.md`](docs/NOTES.md).

## Quick start

```bash
# environments, caches, checkpoints and logs all live here
export EMB_ROOT=/path/to/workdir

# after setting up as described in docs/INSTALL.md:
# ACT, 500 episodes, about 17 minutes on an RTX A5000
bash scripts/eval/run_act.sh
python3 scripts/analysis/summarize_eval.py act_cube_500

# four LIBERO models, every camera black, 100 episodes each
bash scripts/eval/run_blackout_all.sh
python3 scripts/analysis/summarize_blackout.py
```

To regenerate the figures and tables in this README from the evaluation files in `dashboard/data/`, with no GPU and no dependencies:

```bash
python3 dashboard/build.py
python3 scripts/analysis/make_figures.py
```

| Document | Content |
|---|---|
| [`docs/INSTALL.md`](docs/INSTALL.md) | Step-by-step setup of the three conda environments, checkpoints, tokenizer |
| [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) | Every problem hit during setup and evaluation, with cause and fix |
| [`scripts/README.md`](scripts/README.md) | Which entry script and which summary script produce each result |
| [`env/lock/`](env/lock/) | Full package lists exported from the environments that produced the results |

## Repository layout

| Path | Content |
|---|---|
| `scripts/eval/` | Evaluation entry scripts; blackout, perturbation and trajectory-logging wrappers |
| `scripts/analysis/` | Metrics, summaries, figure generation |
| `scripts/checks/` | Self-checks for GPU, headless EGL rendering and video decoding |
| `scripts/train/` | π0 fine-tuning scripts for an experiment recorded in `docs/NOTES.md` (not part of the results above) |
| `results/` | Result tables (CSV) generated from `dashboard/data`, and the trajectories plotted in 1.3 |
| `dashboard/` | Results dashboard and the raw `eval_info.json` of every run |
| `media/` | Figures and demos used in this README (Chinese versions in `media/zh/`) |
| `docs/` | Installation, troubleshooting, reproduction notes |
| `env/` | Environment file, pip constraints, exported package lists |
| `tests/` | Unit tests for the metrics, consistency checks on the published numbers, entry-script regression tests |
| `viewer/` | Replay a policy trajectory locally in the interactive MuJoCo viewer |

## Limitations

- One benchmark suite (LIBERO-Spatial) and one seed.
- The ablations use 100 episodes per run, so differences under about 13 points are not meaningful; for π0, repeated runs of one condition differed by up to 18 points.
- The π0 checkpoint is under-trained. A properly trained π0 may behave differently.
- How much the scene varies between initial states of a task was not measured, so nothing here says how much vision the benchmark itself requires.
- Diffusion Policy was evaluated on PushT (2-D physics), not in MuJoCo.

## Acknowledgements and licenses

This repository contains no model weights and no upstream source code. It builds on:

| Project | Used for | License |
|---|---|---|
| [LeRobot](https://github.com/huggingface/lerobot) v0.6.1 | ACT, Diffusion Policy, SmolVLA, π0, π0.5 evaluation and π0 fine-tuning | Apache-2.0 |
| [OpenVLA](https://github.com/openvla/openvla) | OpenVLA evaluation | MIT |
| [OpenPI](https://github.com/Physical-Intelligence/openpi) | π0 and π0.5 reference numbers | Apache-2.0 |
| [LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO) | benchmark | MIT |
| [Diffusion Policy](https://github.com/real-stanford/diffusion_policy), [ACT](https://github.com/tonyzhaozh/act) | original methods | MIT |
| [MuJoCo](https://github.com/google-deepmind/mujoco), [gym-aloha](https://github.com/huggingface/gym-aloha), [gym-pusht](https://github.com/huggingface/gym-pusht) | simulation | Apache-2.0 |

Checkpoints: `lerobot/act_aloha_sim_transfer_cube_human`, `openvla/openvla-7b-finetuned-libero-spatial`, `lerobot/smolvla_libero`, `lerobot/pi05_libero_finetuned_v044`, `lerobot/pi0_libero_finetuned_v044`, `lerobot/diffusion_pusht`. Exact commits are in [`results/reproduction.csv`](results/reproduction.csv) and [`docs/NOTES.md`](docs/NOTES.md). Each checkpoint has its own license. The π0 tokenizer comes from the gated `google/paligemma-3b-pt-224` repository under the Gemma terms and is not included.

Papers: [ACT](https://arxiv.org/abs/2304.13705) · [Diffusion Policy](https://arxiv.org/abs/2303.04137) · [OpenVLA](https://arxiv.org/abs/2406.09246) · [LIBERO](https://arxiv.org/abs/2306.03310) · [SmolVLA](https://arxiv.org/abs/2506.01844) · [π0](https://arxiv.org/abs/2410.24164) · [π0.5](https://arxiv.org/abs/2504.16054)

## Citation

See [`CITATION.cff`](CITATION.cff), or use GitHub's "Cite this repository" button.
