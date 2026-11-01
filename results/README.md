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
| [state_feedback_episodes.csv](state_feedback_episodes.csv) | All 1240 P1 records, separating smoke/formal and paired states |
| [state_feedback_runs.csv](state_feedback_runs.csv) | P1 group/repeat counts and Wilson intervals |
| [state_feedback_per_task.csv](state_feedback_per_task.csv) | P1 per-task, condition and repeat counts |
| [state_feedback_comparisons.csv](state_feedback_comparisons.csv) | P1 primary/secondary contrasts and exploratory interaction |
| [replay_holdout_episodes.csv](replay_holdout_episodes.csv) | All 410 P2 self/formal outcomes and stopping reasons |
| [replay_holdout_summary.csv](replay_holdout_summary.csv) | P2 per-task Wilson and overall stratified-bootstrap intervals |

## Trace a number

Use a CSV's model, condition, and run identifier to find the corresponding [experiment](../docs/EXPERIMENTS.md), [notes](../docs/NOTES.md), and raw JSON. Checkpoint revisions are recorded in `reproduction.csv` and `RUNS` in [dashboard/build.py](../dashboard/build.py).

Repeating the same initial states does not add independent samples. The LeRobot all-black row in `official_pi0_summary.csv` aggregates five runs; use the paired-comparison scope in the experiment report.

## Regenerate

From the repository root with Python 3.10+. The third command requires NumPy for P1/P2 bootstrap; the first two use the standard library. No GPU or simulation is needed; see the [quick start](../README.md#quick-start):

```bash
python3 dashboard/build.py
python3 scripts/analysis/make_figures.py
python3 scripts/analysis/summarize_followup.py
```

These build dashboard data, earlier CSVs/figures, then P1/P2 CSVs/figures. P1 keeps repeats and paired conditions together within initial state; P2 resamples targets within fixed tasks. Their denominators are separate.

`trajectories_task4.json` and `trajectories_task7.json` contain compact XY trajectories (cm) for the trajectory figure. [export_trajectories.py](../scripts/analysis/export_trajectories.py) exports them separately from raw NPZ files; it needs NumPy and the raw trajectories. The commands above do not regenerate them.

P1/P2 sources are [state_feedback](../dashboard/data/state_feedback/) and [replay_holdout](../dashboard/data/replay_holdout/), with hash-bound run/episode records. Full NPZ files stay outside Git; each directory explains audit scope and missing records.
