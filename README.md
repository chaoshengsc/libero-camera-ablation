# Do robot policies look at the camera?

**Reproducing six open-source robot policies in MuJoCo, then testing how much each one relies on vision.**

[![CI](https://github.com/chaoshengsc/robot-policy-sim-repro/actions/workflows/ci.yml/badge.svg)](https://github.com/chaoshengsc/robot-policy-sim-repro/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Dashboard](https://img.shields.io/badge/results-live%20dashboard-2563eb)](https://chaoshengsc.github.io/robot-policy-sim-repro/dashboard/)

English | [中文](README_CN.md)

<p align="center">
  <img src="media/blackout_demo.gif" width="720" alt="Three rollouts of the same LIBERO task: pi0.5 with cameras succeeds, pi0.5 with black camera input fails, pi0 with black camera input still succeeds">
  <br><sub>Same task, same initial state. The videos show what happened in the simulator; in the two right-hand runs the policy itself received black images.</sub>
</p>

- **Reproduction.** ACT, OpenVLA, π0.5 and Diffusion Policy reproduce their reference success rates within error. The public π0 and SmolVLA checkpoints do not (73% vs. 97%, 75% vs. 90%).
- **Vision dependence.** With every camera image replaced by black frames, π0.5, OpenVLA and SmolVLA drop to 0%. π0 still succeeds 56% of the time.
- **Why.** π0 ignores the main camera, is unaffected by a frozen image, and leans on the robot-state input. Zeroing that input during fine-tuning makes it depend on vision more.

Everything runs on one workstation (RTX A5000 24 GB, Ubuntu 24.04, headless EGL rendering), with public checkpoints and wrapper scripts that leave upstream source untouched.

**Contents:** [Reproduction](#1-reproduction) · [Vision dependence](#2-do-the-policies-use-the-camera) · [Quick start](#quick-start) · [Layout](#repository-layout) · [Limitations](#limitations) · [Acknowledgements](#acknowledgements-and-licenses)

## 1. Reproduction

![Success rate on this machine vs. reference](media/reproduction.svg)

| Model | Task | This machine (500 episodes) | Reference | Reproduced |
|---|---|---|---|---|
| ACT | ALOHA Transfer Cube | **83.2%** | 83.0% (Hugging Face repo) | ✅ |
| OpenVLA | LIBERO-Spatial | **86.2%** | 84.7 ± 0.9% (official README) | ✅ |
| π0.5 | LIBERO-Spatial | **98.0%** | 98.8% (OpenPI), 97.0% (LeRobot) | ✅ |
| Diffusion Policy | PushT | **63.0%** | 65.4% (LeRobot model card) | ✅ |
| SmolVLA | LIBERO-Spatial | 75.2% | 90% (paper) | ❌ |
| π0 | LIBERO-Spatial | 73.4% | 96.8% (OpenPI) | ❌ |

The 95% confidence interval at 500 episodes is about ±3–4 points. "Reproduced" means the intervals overlap.

<p align="center"><img src="media/act_transfer_cube_success.gif" width="320" alt="A successful ACT episode"><br><sub>ACT on ALOHA Transfer Cube: the right arm picks up the cube and hands it to the left arm.</sub></p>

Why two fail:

- **π0.** The reference number is for OpenPI's own checkpoint. A LeRobot maintainer has confirmed that the LeRobot checkpoint used here is under-trained, and the community reports 73% for it.
- **SmolVLA.** The public checkpoint has a different architecture from the paper (expert width 0.5 and 32 VLM layers, vs. 0.75 and 16). The community reports about 82% for it; this machine is still 7 points below that, and the cause is not found. Batch size and `n_action_steps` were ruled out.

Changing π0's `n_action_steps` from 5 to 10 or 50 gives 76%, 70% and 68% (100 episodes each), which is within noise.

Per-task results and replays are on the [dashboard](https://chaoshengsc.github.io/robot-policy-sim-repro/dashboard/). Sources and debugging history are in [`docs/NOTES.md`](docs/NOTES.md) (Chinese).

## 2. Do the policies use the camera?

A LIBERO policy receives two camera images, the robot state and a language instruction. Each experiment below changes one of these.

![What the policy receives and what each experiment changes](media/inputs.svg)

All numbers in this section are success rates over 100 episodes (10 tasks × 10 initial states, same seed for every condition). The 95% confidence interval is about ±9 points.

### 2.1 Black out every camera

| Model | Normal | All cameras black |
|---|---|---|
| π0.5 | 99% | 0% |
| OpenVLA | 81% | 0% |
| SmolVLA | 72% | 0% |
| **π0** | 76% | **56%** |

Three models cannot act without images. π0 completes more than half of the tasks blind, which matches the report in lerobot issue #3591.

### 2.2 Which camera, and what kind of perturbation?

![Success rate under each perturbation](media/perturbations.svg)

| Model | Normal | Gaussian noise | Frozen first frame | Agent-view black | Wrist black | All black |
|---|---|---|---|---|---|---|
| π0 | 76% | 79% | 71% | 78% | 59% | 56% |
| π0.5 | 99% | 99% | 0% | 51% | 0% | 0% |
| SmolVLA | 72% | 32% | running | 2% | 5% | 0% |

- **π0** does not use the agent-view camera at all (78% with it black) and barely needs a live image: showing it only the first frame for the whole episode costs 5 points.
- **π0.5** is closed-loop on vision. Noise does nothing, but a frozen image or a black wrist camera takes it to 0%.
- **SmolVLA** breaks under every perturbation, including mild noise, which points to sensitivity to out-of-distribution input.

Noise is Gaussian with standard deviation 0.1 on pixels in [0, 1].

### 2.3 Is blind π0 replaying a memorised trajectory?

No. The end-effector position was logged at every step and paths were compared with dynamic time warping, which removes speed differences.

![End-effector paths of pi0 with and without camera input](media/trajectory.svg)

| Comparison | Path difference | Grasp-point distance |
|---|---|---|
| π0 normal vs. π0 normal re-run (noise floor) | 2.12 cm | 1.51 cm |
| **π0 all black vs. π0 normal** | **4.44 cm** | **5.03 cm** |
| π0.5 vs. π0, both normal | 3.28 cm | 2.65 cm |

Blind π0 takes a different path from sighted π0, about twice the noise floor. Its grasp points do not collapse onto one spot either, so it is not executing one fixed "average" motion.

The likelier explanation is the benchmark. Within a LIBERO-Spatial task the grasp point varies by only about 1.8 cm across initial states, the same order as the model's own run-to-run noise. A policy that misses by 5 cm still succeeds about half the time.

### 2.4 Can training make π0 look?

The public π0 checkpoint was fine-tuned for 3000 more steps (batch 16, action expert only, about 15% of the original training). The treatment group had `observation.state` zeroed for 50% of training samples.

| Model | Normal | All cameras black |
|---|---|---|
| Original π0 | 76% | 56% |
| Fine-tuned, control | 78% | 61% |
| Fine-tuned, state zeroing | 68% | **40%** |

Blind success falls from 61% to 40% (z ≈ 3.0, p ≈ 0.003), so the model now relies on vision more. Normal success falls from 78% to 68%, which is not significant (p ≈ 0.11). The training loss jumps from 0.145 to 0.835 the first time the state is removed, which shows how much the original π0 depended on it.

A 10,000-step version of this experiment is running; results will be added here.

## Quick start

```bash
export EMB_ROOT=/path/to/workdir      # environments, caches, checkpoints and logs all live here
# after installing the environments and downloading checkpoints (docs/INSTALL.md):
bash scripts/eval/run_act.sh          # ACT, 500 episodes, about 17 minutes on an RTX A5000
python3 scripts/analysis/summarize_eval.py act_cube_500
```

To regenerate the figures and tables in this README from the raw evaluation files, with no GPU and no dependencies:

```bash
python3 dashboard/build.py && python3 scripts/analysis/make_figures.py
```

| Document | Content |
|---|---|
| [`docs/INSTALL.md`](docs/INSTALL.md) | Step-by-step setup of the three conda environments, checkpoints, tokenizer (Chinese) |
| [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) | Every problem hit during setup and evaluation, with cause and fix (Chinese) |
| [`scripts/README.md`](scripts/README.md) | Which entry script and which summary script produce each result (Chinese) |
| [`env/lock/`](env/lock/) | Full package lists exported from the environments that produced the results |

## Repository layout

```
scripts/eval/      evaluation entry scripts; blackout, perturbation and trajectory-logging wrappers
scripts/train/     π0 fine-tuning with state zeroing, and the automated pipeline
scripts/analysis/  metrics, summaries, figure generation
scripts/checks/    self-checks for GPU, headless EGL rendering and video decoding
results/           result tables (CSV) and trajectory data, generated from dashboard/data
dashboard/         results dashboard and the raw eval_info.json of every run
media/             figures and demos used in this README (Chinese versions in media/zh/)
docs/              installation, troubleshooting, reproduction notes
env/               environment file, pip constraints, exported package lists
tests/             unit tests for the metrics and consistency checks on the published numbers
viewer/            replay a policy trajectory locally in the interactive MuJoCo viewer
```

## Limitations

- One benchmark suite (LIBERO-Spatial) and one seed. The scene varies little within a task, which is itself part of the finding in 2.3.
- The vision-dependence experiments use 100 episodes per condition, so differences under about 10 points are not meaningful.
- The π0 checkpoint is under-trained. A properly trained π0 may behave differently.
- The SmolVLA gap to the community number is unexplained.
- Fine-tuning in 2.4 was short and trained the action expert only.

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

Checkpoints: `lerobot/act_aloha_sim_transfer_cube_human`, `openvla/openvla-7b-finetuned-libero-spatial`, `HuggingFaceVLA/smolvla_libero`, `lerobot/pi05_libero_finetuned_v044`, `lerobot/pi0_libero_finetuned_v044`, `lerobot/diffusion_pusht`. Exact commits are in [`results/reproduction.csv`](results/reproduction.csv). Each checkpoint has its own license. The π0 tokenizer comes from the gated `google/paligemma-3b-pt-224` repository under the Gemma terms and is not included.

Papers: [ACT](https://arxiv.org/abs/2304.13705) · [Diffusion Policy](https://arxiv.org/abs/2303.04137) · [OpenVLA](https://arxiv.org/abs/2406.09246) · [LIBERO](https://arxiv.org/abs/2306.03310) · [SmolVLA](https://arxiv.org/abs/2506.01844) · [π0](https://arxiv.org/abs/2410.24164) · [π0.5](https://arxiv.org/abs/2504.16054)

## Citation

See [`CITATION.cff`](CITATION.cff), or use GitHub's "Cite this repository" button.
