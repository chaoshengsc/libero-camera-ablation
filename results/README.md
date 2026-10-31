# Results directory

[中文](README_CN.md) · [Project overview](../README.md) · [Docs & data](../docs/README.md)

Recomputable tables live here. Read the [experiments](../docs/EXPERIMENTS.md) for methods and comparison scope. Raw evaluations are under [dashboard/data/](../dashboard/data/).

## Find a result

| File | Contents |
|---|---|
| [reproduction.csv](reproduction.csv) | Five public checkpoints, references, and confidence intervals |
| [blackout_per_task.csv](blackout_per_task.csv) | Per-task success counts with normal and black camera input |
| [perturbations.csv](perturbations.csv) | Noise, frozen frames, one-camera blackout, and repeats |
| [trajectory.csv](trajectory.csv) | Two trajectory comparisons, DTW, and grasp-point differences |
| [single_camera_summary.csv](single_camera_summary.csv) | 500-episode single-camera summaries and paired statistics |
| [single_camera.csv](single_camera.csv) | Single-camera episode outcomes and first-frame hashes |
| [official_pi0_summary.csv](official_pi0_summary.csv) | Official/OpenPI, LeRobot, and rendering controls |
| [open_loop_replay.csv](open_loop_replay.csv) | Self-replay, cross-replay, and post-hoc selection bias |

## Trace a number

Use a CSV's model, condition, and run identifier to find the corresponding [experiment](../docs/EXPERIMENTS.md), [notes](../docs/NOTES.md), and raw JSON. Checkpoint revisions are recorded in `reproduction.csv` and `RUNS` in [dashboard/build.py](../dashboard/build.py).

Repeating the same initial states does not add independent samples. The LeRobot all-black row in `official_pi0_summary.csv` aggregates five runs; use the paired-comparison scope in the experiment report.

## Regenerate

From the repository root, with Python 3.10+ and the standard library, without a GPU:

```bash
python3 dashboard/build.py
python3 scripts/analysis/make_figures.py
```

The first builds dashboard data; the second updates the CSVs here and the figures under `media/`.

`trajectories_task4.json` and `trajectories_task7.json` contain compact XY trajectories (cm) for the trajectory figure. [export_trajectories.py](../scripts/analysis/export_trajectories.py) exports them separately from raw NPZ files; it needs NumPy and the raw trajectories. The commands above do not regenerate them.
