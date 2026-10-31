# Docs & data guide

[中文](README_CN.md) · [Project overview](../README.md) · [Interactive results](https://chaoshengsc.github.io/libero-camera-ablation/dashboard/?lang=en)

The README presents the key findings. This guide connects the full study, reproduction steps, and evidence. Notes retain historical judgments and later corrections; use the experiment report and raw records for result context.

| Goal | Document | Contents |
|---|---|---|
| Understand the study | [Experiments & results](EXPERIMENTS.md) | Interventions, full tables, repeated runs, and interpretation limits |
| Set up | [Installation](INSTALL.md) | Environments, checkpoints, tokenizer, and a first evaluation |
| Choose an entry point | [Script index](../scripts/README.md) | Reproduction, camera ablations, official π0, and analysis |
| Resolve a failure | [Troubleshooting](TROUBLESHOOTING.md) | Symptoms, causes, and fixes |
| Verify a number | [Results directory](../results/README.md) | Table purposes, raw evidence, and generation commands |
| Trace the history | [Notes & corrections](NOTES.md) | Chronological designs, failures, revisions, and run records |

## Common paths

- **Understand the findings:** [README](../README.md) → [Full experiments](EXPERIMENTS.md) → [Limitations](../README.md#limitations).
- **Reproduce a model:** [Install](INSTALL.md) → [Environment guide](../env/README.md) → [Script index](../scripts/README.md).
- **Audit a number:** [Result CSVs](../results/README.md) → [Raw evaluations](../dashboard/data/) → [Designs & corrections](NOTES.md).

## Experiments and evidence

| Experiment | Result tables | Raw-evidence entry |
|---|---|---|
| [All black](EXPERIMENTS.md#11-all-cameras-black) | [blackout_per_task.csv](../results/blackout_per_task.csv) | [Raw records](../dashboard/data/) |
| [Noise & frozen frames](EXPERIMENTS.md#12-one-camera-noise-frozen-image) | [perturbations.csv](../results/perturbations.csv) | [Raw records](../dashboard/data/run2/) |
| [Trajectories](EXPERIMENTS.md#13-where-blind-π0-succeeds-it-follows-the-sighted-path) | [trajectory.csv](../results/trajectory.csv) | [Raw records](../dashboard/data/traj_analyze.json) |
| [Single camera](EXPERIMENTS.md#14-wrist-camera-removed-500-episodes) | [single_camera_summary.csv](../results/single_camera_summary.csv) | [Raw records](../dashboard/data/s500/) |
| [Official π0](EXPERIMENTS.md#15-official-π0-control) | [official_pi0_summary.csv](../results/official_pi0_summary.csv) | [Raw records](../dashboard/data/official_pi0/) |
| [Fixed-action replay](EXPERIMENTS.md#16-fixed-action-replay) | [open_loop_replay.csv](../results/open_loop_replay.csv) | [Raw records](../dashboard/data/official_pi0/ojx360_replay/replay.json) |
| [Public-checkpoint reproduction](EXPERIMENTS.md#2-reproduction-of-the-public-checkpoints) | [reproduction.csv](../results/reproduction.csv) | [Raw records](../dashboard/build.py) |

## Update the results

From the repository root, run `python3 dashboard/build.py`, then `python3 scripts/analysis/make_figures.py`. They update dashboard data, CSVs, and bilingual SVGs without a model evaluation.

[tests/](../tests/) and [CI](../.github/workflows/ci.yml) check derived numbers against raw records. See the [script index](../scripts/README.md) for evaluation entry points and adding a new result.

<details>
<summary>Updates & corrections</summary>

- **2026-10-29** · Official π0 control ([section 1.5](EXPERIMENTS.md#15-official-π0-control)): OpenPI itself scores 96.4% normally and 0% without vision; 0% with only the wrist camera masked, 77% with only the main view masked. Earlier versions called LeRobot's π0 checkpoint "under-trained"; this repository never tested that, and the wording is replaced by facts.
- **2026-10-28** · Single-camera experiment, 500 episodes per condition ([section 1.4](EXPERIMENTS.md#14-wrist-camera-removed-500-episodes)). While setting it up, found that LeRobot silently shifts camera slots when a camera is missing: reported as [lerobot#5118](https://github.com/huggingface/lerobot/issues/5118), fix proposed in [lerobot#5129](https://github.com/huggingface/lerobot/pull/5129).
- **2026-10-14** · [v1.3](https://github.com/chaoshengsc/libero-camera-ablation/releases/tag/v1.3): every ablation run a second time; the claim that π0 depends on the wrist camera was withdrawn.
- **2026-10-07** · [v1.2](https://github.com/chaoshengsc/libero-camera-ablation/releases/tag/v1.2): repository renamed; SmolVLA ablations re-run with the checkpoint used in the reproduction table.

</details>
