<div align="center">

# Do robot policies actually use their cameras?

Camera ablations of four robot policies on LIBERO-Spatial

[![CI](https://github.com/chaoshengsc/libero-camera-ablation/actions/workflows/ci.yml/badge.svg)](https://github.com/chaoshengsc/libero-camera-ablation/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/chaoshengsc/libero-camera-ablation?color=2563eb)](https://github.com/chaoshengsc/libero-camera-ablation/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

**English** · [中文](README_CN.md)

[Findings](#1-camera-ablations) · [Reproduction](#2-reproduction-of-the-public-checkpoints) · [Quick start](#quick-start) · [Data](results/README.md) · [Docs](docs/README.md)

</div>

**Does completing a simulated task mean a robot uses its cameras?** We ablate camera inputs for public π0, π0.5, OpenVLA, and SmolVLA checkpoints, then use an official π0 control, fixed-action replay and state-input checks to bound the interpretation. Evaluation of five public checkpoints against published references provides the engineering foundation.

**In the tested all-black episodes, the π0.5, OpenVLA and SmolVLA checkpoints score 0%. LeRobot π0 v044 scores 53–56% across five runs; official π0 in OpenPI scores 0/100.**

<p align="center">
  <img src="media/blackout_demo.gif" width="720" height="300" alt="Same LIBERO task: π0.5 succeeds with normal vision and fails with black input; LeRobot π0 still succeeds with black input">
  <br><sub>Same task and initial state. The two right-hand policies receive black images; the videos show their actual actions in the simulator.</sub>
</p>

| Your goal | Start here |
|---|---|
| Understand the findings | [Key findings](#1-camera-ablations) → [Full experiments & figures](docs/EXPERIMENTS.md) |
| Reproduce an experiment | [Install](docs/INSTALL.md) → [Script index](scripts/README.md) → [Troubleshoot](docs/TROUBLESHOOTING.md) |
| Verify a number | [Result tables](results/README.md) → [Raw evaluations](dashboard/data/) → [Notes & corrections](docs/NOTES.md) |

[Docs & data guide](docs/README.md) · [Interactive results](https://chaoshengsc.github.io/libero-camera-ablation/dashboard/?lang=en) · [Repository layout](#repository-layout) · [Limitations](#limitations)

## 1. Camera ablations

### All cameras black

| Policy | Normal vision | All cameras black |
|---|---|---|
| π0.5 | 99% | 0% |
| OpenVLA | 81% | 0% |
| SmolVLA | 83% | 0% |
| **π0 · LeRobot v044** | 76% | **56%** |

These are representative 100-episode runs. Normal vision uses the first 10 episodes per task of each 500-episode evaluation. The first three policies also score 0% in a repeat.

π0 scores **53–56%** across five all-black runs. They use the same 100 initial states, so they are not 500 independent states.

<a id="15-official-π0-control"></a>

### Official π0 control

![Official π0 and LeRobot π0 camera-ablation comparison](media/official_pi0.svg)

With normal vision, official π0 in OpenPI scores **96.4%** and LeRobot π0 v044 in LeRobot scores **72.0%** (500 episodes each). With all cameras black, they score **0/100** and **53–56%** across five LeRobot runs, respectively.

**In these all-black comparisons, LeRobot π0 v044 with its pipeline retains successful episodes; official π0/OpenPI has none.**

Both the weights and the inference pipeline differ between the two sides; the difference cannot be attributed to the weights alone.

A re-run of official π0 at 360 rendering still scores 0/100 with black input; this resolution change did not restore success. Further checks add context:

- **Image-freezing sensitivity.** The tested π0.5 and SmolVLA checkpoints score 0% with frozen first frames in both runs. Masking the wrist camera in its original slot brings π0.5 from 98.4% to 4.6% (500 episodes per condition). Freezing changes both visual updates and image–state synchronization; their effects remain unseparated.
- **Fixed actions also succeed.** P2 replays one preselected official π0 sequence per task on states excluded from action selection: **262/400 = 65.5%**, with a **61.0–69.8%** stratified-bootstrap interval and **10/10** self-replay checks. This strengthens the baseline without identifying the LeRobot π0 mechanism. [Protocol, earlier replay and limits](docs/EXPERIMENTS.md#16-fixed-action-replay).
- **State updates still matter.** In P1, LeRobot π0 v044 averages **73.3% / 55.3%** with normal/black images across three repeats; both score **0%** when the model receives its frozen first state. This measures update sensitivity, not a unique correction or phase mechanism. [Paired statistics](docs/EXPERIMENTS.md#17-state-input-update-sensitivity).

See the [full experiments](docs/EXPERIMENTS.md) for designs, repeated runs, per-task results, and statistical scope. The [notes](docs/NOTES.md) retain chronological records and corrections.

## 2. Reproduction of the public checkpoints

| Model | Task | This repo (500 episodes) | Reference | Repo criterion |
|---|---|---|---|---|
| ACT | ALOHA Transfer Cube | **83.2%** | 83.0% (Hugging Face repo) | ✅ |
| OpenVLA | LIBERO-Spatial | **86.2%** | 84.7 ± 0.9% (official README) | ✅ |
| SmolVLA | LIBERO-Spatial | **85.4%** | 90% (paper, 100 episodes) | ✅ |
| π0.5 | LIBERO-Spatial | **98.0%** | 98.8% (OpenPI), 97.0% (LeRobot) | ✅ |
| Diffusion Policy | PushT (2-D, not MuJoCo) | **63.0%** | 65.4% (LeRobot model card) | ✅ |

This repository compares its 95% confidence interval with a reference range: a reported ± value, an interval estimated from an available episode count, or a single point when no range is available. Overlap meets this repository's “reproduction” criterion. This is a reference-comparison convention, not a performance-equivalence test or a claim to reproduce identical training configurations. Each evaluation has 500 episodes, giving this repository's interval of about ±1–4 points.

SmolVLA uses `lerobot/smolvla_libero` with `n_action_steps=10`, trained on LIBERO-Spatial only. The paper trains on four suites; its 100-episode reference has an interval of about ±6 points.

See [reproduction details](docs/EXPERIMENTS.md#2-reproduction-of-the-public-checkpoints) for the full reference context.

## Quick start

**Recompute included results first: no GPU or model weights required.** From the repository root, with Python 3.10+:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install numpy
python dashboard/build.py
python scripts/analysis/make_figures.py
python scripts/analysis/summarize_followup.py
```

The first three commands create/activate a local analysis environment and install NumPy for the P1/P2 bootstrap; skip them if your environment is ready. The last three build dashboard data, the original tables/figures, and the P1/P2 episode tables and grouped intervals. Outputs are in [results/](results/README.md) and [media/](media/); the [data guide](docs/README.md#experiments-and-evidence) links their sources.

For a missing NumPy import, check the active environment. Missing raw files require checking the checkout, not another model run.

**Run a camera ablation:** configure Ubuntu/EGL, `EMB_ROOT` and the checkpoint using [installation](docs/INSTALL.md), then follow the [minimal camera evaluation](scripts/README.md#minimal-camera-evaluation). It runs ten simulation episodes as an entry-point check. Full reproduction, P1 and P2 entries are in the [script index](scripts/README.md).

## Repository layout

```text
libero-camera-ablation/
├── README.md / README_CN.md   Project overview and key findings
├── docs/                     Full experiments, setup, troubleshooting, history
├── scripts/                  Evaluation, interventions, summaries, figures
├── env/                      Configuration, constraints, package inventories
├── results/                  Recomputable result tables and trajectory data
├── media/                    Figures and demos; Chinese assets in zh/
├── dashboard/                Interactive results and data builder
│   └── data/                 Raw evaluations and diagnostics
├── viewer/                   Local MuJoCo trajectory viewer
├── tests/                    Metrics and published-number consistency
└── .github/                  CI and issue templates
```

[Document map](docs/README.md) · [Execution entry points](scripts/README.md) · [Results directory](results/README.md) · [Environment directory](env/README.md)

## Limitations

- Camera studies cover LIBERO-Spatial only. Earlier camera runs fix the environment seed; P1 adds three policy-noise repeats on the same 100 initial states, without new tasks or real robots.
- [Experiments 1.1–1.3](docs/EXPERIMENTS.md#11-all-cameras-black) use 100 episodes per run; the [single-camera study](docs/EXPERIMENTS.md#14-wrist-camera-removed-500-episodes) uses 500. Repeating initial states does not add independent samples. Comparisons depend on pairing and repeat structure, not a universal 13-point threshold. Earlier π0 repeats of one condition differed by up to 18 points.
- The π0 results concern the tested checkpoint/pipeline combinations. The official control uses the OpenPI path that passed the normal-evaluation gate; the LeRobot conversion scored 0/50 in smoke testing and failed acceptance. Official π0 scores 0/100 with black input at both 256 and 360 rendering; this check does not isolate weights, conversion or other inference differences. Each official π0 ablation condition was run once, 100 episodes.
- [Replay](docs/EXPERIMENTS.md#16-fixed-action-replay) concerns the selected sequences and states. P2 targets were excluded from action selection but had appeared in earlier evaluations; they are not a hidden test set. P1/P2 use different checkpoint/state protocols and cannot be subtracted to assign mechanism contributions. P1 lacks stepwise terminal flags and full images; state freezing does not identify a unique mechanism. Full NPZ audit artifacts remain outside Git; published records reproduce rates and intervals.
- Diffusion Policy was evaluated on PushT (2-D physics), not in MuJoCo.

## Acknowledgements and licenses

Code is [MIT licensed](LICENSE). Upstream projects, checkpoints, and the tokenizer retain their own terms. Model weights and the tokenizer are not included.

<details>
<summary>Upstream projects, checkpoints, and papers</summary>

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

</details>

## Citation

If you use these results or scripts, please cite:

```bibtex
@software{shengchao2026liberocameraablation,
  author  = {ShengChao},
  title   = {libero-camera-ablation: Camera-input ablations of four robot policies on LIBERO-Spatial},
  year    = {2026},
  version = {1.4.0},
  url     = {https://github.com/chaoshengsc/libero-camera-ablation}
}
```

The same entry is in [`CITATION.cff`](CITATION.cff), which GitHub's "Cite this repository" button reads.
