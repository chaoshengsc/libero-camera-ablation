# Script index

[中文](README_CN.md) · [Project overview](../README.md) · [Docs & data](../docs/README.md)

Choose an entry point by the result you want to reproduce. Tables link to source files; use their headers and usage messages for arguments. Command paths are relative to the repository root.

## Prerequisites

Complete [installation](../docs/INSTALL.md) and [environment configuration](../env/README.md), set `EMB_ROOT`, and prepare the checkpoint. Shell evaluation entries load [common.sh](common.sh), then `$EMB_ROOT/env.sh` and local checkpoint paths.

Wrappers replace functions at run time without changing LeRobot / OpenVLA sources. Model-evaluation entries and analysis of existing data are listed separately below.

## Public-checkpoint reproduction

| Model / task | Entry point | Summary |
|---|---|---|
| ACT · ALOHA Transfer Cube | [run_act.sh](eval/run_act.sh) | [summarize_eval.py](analysis/summarize_eval.py) |
| Diffusion Policy · PushT | [run_dp_pusht.sh](eval/run_dp_pusht.sh) | [summarize_eval.py](analysis/summarize_eval.py) |
| OpenVLA · LIBERO-Spatial | [run_ovla.sh](eval/run_ovla.sh) | [ovla_to_json.py](analysis/ovla_to_json.py) |
| SmolVLA / π0 / π0.5 · LIBERO-Spatial | [run_libero.sh](eval/run_libero.sh) | [summarize_eval.py](analysis/summarize_eval.py) |

`run_libero.sh` takes a run name, episodes per task, checkpoint directory, and batch size, followed by optional evaluation arguments. Fifty episodes for each of the ten LIBERO tasks gives 500 episodes.

The reproduction table uses `lerobot/smolvla_libero`. Its extra arguments are defined as `SMOL2_ARGS` in `common.sh`:

- `--policy.n_action_steps=10`.
- `--rename_map` maps `observation.images.image` / `image2` to `observation.images.camera1` / `camera2`.
- The base model `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` must be in the Hugging Face cache.

## Camera ablations and official π0

| Experiment | Entry point | Results and interpretation |
|---|---|---|
| All cameras black, four policies | [run_blackout_all.sh](eval/run_blackout_all.sh) | [summarize_blackout.py](analysis/summarize_blackout.py) · [Experiment 1.1](../docs/EXPERIMENTS.md#11-all-cameras-black) |
| Noise and frozen first frames | [run_perturbation.sh](eval/run_perturbation.sh) | [Experiment 1.2](../docs/EXPERIMENTS.md#12-one-camera-noise-frozen-image) |
| End-effector trajectories, one-camera blackout | [run_trajectory_and_single_camera.sh](eval/run_trajectory_and_single_camera.sh) | [Trajectory analysis](analysis/analyze_trajectories.py) · [Single-camera summary](analysis/summarize_single_camera.py) |
| Official π0 control, single-camera masks, freeze, replay | [run_official_pi0.sh](eval/run_official_pi0.sh) | [Experiments 1.5–1.6](../docs/EXPERIMENTS.md#15-official-π0-control) |

The official OpenPI π0 path needs a separate environment and an active local [serve_pi0_libero.py](openpi/serve_pi0_libero.py) server. [download_checkpoint.py](openpi/download_checkpoint.py) is the checkpoint download entry.

Read the staged runner and [notes](../docs/NOTES.md) for the protocol. This is a different inference pipeline from the LeRobot conversion.

## Intervention configuration

`WRAP` in [run_libero.sh](eval/run_libero.sh) chooses the evaluator:

| `WRAP` | Entry | `BLACKOUT` |
|---|---|---|
| `none` (default) | `lerobot-eval` | No camera intervention |
| `blackout` | [eval_blackout.py](eval/eval_blackout.py) | `all`, `agent`, `wrist` |
| `probe` | [eval_probe.py](eval/eval_probe.py) | See below; also records `traj.npz` |

`probe` supports `none`, `all`, `agent`, `wrist`, `noise`, `freeze`, `drop_wrist`, `drop_agent`, `drop_all`, `freeze_wrist`, and `freeze_agent`.

`drop_*` masks the original camera slot rather than deleting a dictionary key. `freeze_*` uses the real first frame of the episode. Wrapper assertions define the supported models and mask checks.

These interventions are not interchangeable. See the [experiment report](../docs/EXPERIMENTS.md) for comparison scope.

## Existing-data analysis and figures

| Goal | Entry | Required input |
|---|---|---|
| Rebuild dashboard data | [dashboard/build.py](../dashboard/build.py) | Included raw evaluation JSONs; standard library |
| Generate CSVs / bilingual SVGs | [make_figures.py](analysis/make_figures.py) | Dashboard data and included trajectory summaries; standard library |
| Compare end-effector paths | [analyze_trajectories.py](analysis/analyze_trajectories.py) | Raw `traj.npz` and NumPy |
| Export figure data for tasks 4 / 7 | [export_trajectories.py](analysis/export_trajectories.py) | Raw `traj.npz` and NumPy |
| Compare video frames | [compare_videos.py](analysis/compare_videos.py) | Videos from corresponding runs |
| Metric implementations | [metrics.py](analysis/metrics.py) | CI, two-proportion tests, DTW, grasp point; checked by [tests/](../tests/) |

To add a result, place its `eval_info.json` under `dashboard/data/<run>/`, register the run in `dashboard/build.py`, and run the commands below. Specialized comparisons also need their paired outcomes and hash records; a success rate alone is insufficient.

```bash
python3 dashboard/build.py
python3 scripts/analysis/make_figures.py
```

Run both from the repository root to update dashboard data and figures. The [results guide](../results/README.md) lists outputs; [CI](../.github/workflows/ci.yml) checks generation consistency.

## Checks, diagnostics, and historical experiments

- **Environment checks:** [torch_check.py](checks/torch_check.py), [egl_smoke.py](checks/egl_smoke.py), and [codec_check.py](checks/codec_check.py) check GPU/torch, EGL, and video decoding.
- **π0 diagnostics:** [run_pi0_full.sh](eval/run_pi0_full.sh) and [run_pi0_action_steps.sh](eval/run_pi0_action_steps.sh) cover historical smoke/full evaluations and action-chunk checks.
- **Historical fine-tuning:** [run_statedrop_pipeline.sh](train/run_statedrop_pipeline.sh) calls [run_train.sh](train/run_train.sh); [summarize_statedrop.py](analysis/summarize_statedrop.py) summarizes the results. Outcomes and corrections remain in the [notes](../docs/NOTES.md), outside the README's main findings.
