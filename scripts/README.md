# Script index

[中文](README_CN.md) · [Project overview](../README.md) · [Docs & data](../docs/README.md)

Choose an entry point by the result you want to reproduce. Tables link to source files; use their headers and usage messages for arguments. Command paths are relative to the repository root.

## Prerequisites

Recomputing included data needs neither a model, EGL nor `EMB_ROOT`; prepare the NumPy analysis environment in the [quick start](../README.md#quick-start). The prerequisites below apply to evaluation.

Complete [installation](../docs/INSTALL.md) and [environment configuration](../env/README.md), set `EMB_ROOT`, and prepare the checkpoint. Shell evaluation entries load [common.sh](common.sh), then `$EMB_ROOT/env.sh` and local checkpoint paths.

Wrappers replace functions at run time without changing LeRobot / OpenVLA sources. Model-evaluation entries and analysis of existing data are listed separately below.

Run directories are created atomically. Existing directories, files and symlinks (including dangling links) are rejected; failed runs are retained. Names accept only letters, digits, underscores, hyphens and dots, excluding `.` and `..`. Extra arguments to `run_libero.sh` and `run_train.sh` cannot override `--output_dir`.

Command exit codes are preserved and logged as `exit=<code>` in `stdout.log`. Pipelines propagate child failures and do not write a success marker after a failed required stage. The historical training pipeline retains its intended batch16-to-batch8 timing fallback. Parallel/training pipelines retain `.*.started` directories as launch records and reject reuse of their fixed outputs, shared logs and completion markers.

New ACT outputs use `logs/eval/act_cube_500/stdout.log` and `out/`; the old `logs/act_500.log` is untouched. Choose unused names through the named LIBERO, OpenVLA or training entries for another run. ACT, DP and batch entries use fixed names and reject reruns in place; do not delete old artifacts to bypass protection.

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
- Cache `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` at the fixed revision and verify its local main alias using [offline preparation](../docs/INSTALL.md#41-prepare-for-offline-evaluation).

## Convert and summarize existing results

These tools process existing files without a model or simulator. Run-name lookup requires `EMB_ROOT`; `summarize_eval.py --file` reads an explicit JSON without the workstation environment.

```bash
RUN=openvla_spatial_500
python scripts/analysis/ovla_to_json.py "$RUN" novideo
python scripts/analysis/summarize_eval.py --file \
  "$EMB_ROOT/logs/eval/$RUN/dash/eval_info.json"
```

Run from the repository root. Conversion reads the unique `.txt` under `logs/eval/$RUN/logs/`, validates Task/video/Success blocks, then creates a new `dash/`. `novideo` only skips video copying; omitting it selects the first success/failure video per task and checks selected files before creating output. Result JSON is written last. A failed copy retains the failed output directory and artifacts.

Existing directories, files and symlinks, including dangling links, are rejected; old `dash/` is never deleted. For another conversion, pass an unused directory such as `--output "$EMB_ROOT/logs/eval/$RUN/dash_check_01"`. With multiple logs, select `--log FILE` explicitly rather than silently taking the first. Exceptions, empty logs and incomplete episode blocks fail. Still verify planned task/episode coverage and the original evaluation exit status manually: complete blocks can come from a partial run.

The original `python scripts/analysis/summarize_eval.py RUN [RUN ...]` remains supported. Each run must contain exactly one `eval_info.json`; select `--file PATH` if there are several. The tool checks overall counts/rate against per-task outcomes and accepts converted OpenVLA results without timing fields.

Exit codes: **0** means all selected inputs were processed; **1** means missing, ambiguous or invalid data, or an I/O failure; **2** means invalid arguments or required environment configuration. Batch summaries still show valid runs but return 1 if any input fails. Intervals retain the historical binomial normal approximation; use the specialized results for official Wilson intervals and P1/P2 paired bootstrap. A generic summary is not an experiment-acceptance gate.

## Camera ablations and official π0

| Experiment | Entry point | Results and interpretation |
|---|---|---|
| All cameras black, four policies | [run_blackout_all.sh](eval/run_blackout_all.sh) | [summarize_blackout.py](analysis/summarize_blackout.py) · [Experiment 1.1](../docs/EXPERIMENTS.md#11-all-cameras-black) |
| Noise and frozen first frames | [run_perturbation.sh](eval/run_perturbation.sh) | [Experiment 1.2](../docs/EXPERIMENTS.md#12-one-camera-noise-frozen-image) |
| End-effector trajectories, one-camera blackout | [run_trajectory_and_single_camera.sh](eval/run_trajectory_and_single_camera.sh) | [Trajectory analysis](analysis/analyze_trajectories.py) · [Single-camera summary](analysis/summarize_single_camera.py) |
| Official π0 control, single-camera masks, freeze, replay | [run_official_pi0.sh](eval/run_official_pi0.sh) | [Experiments 1.5–1.6](../docs/EXPERIMENTS.md#15-official-π0-control) |

Follow the [official OpenPI installation and reproduction guide](../docs/OPENPI.md) for the separate JAX environment, native checkpoint/tokenizer cache, configuration-only client and local [serve_pi0_libero.py](openpi/serve_pi0_libero.py) server. [download_checkpoint.py](openpi/download_checkpoint.py) downloads native assets.

The guide maps every historical stage to run names, episode counts and rendering settings. The runner does not start the server or enforce the ≥92% success-rate gate; acceptance requires reviewing the actual records. This is a different inference pipeline from the failed LeRobot conversion; the [notes](../docs/NOTES.md) preserve the history.

## Minimal camera evaluation

From the isolated checkout root, after configuring the environment, checkpoint and `EMB_ROOT`:

```bash
CK="$EMB_ROOT/ckpt/pi0_libero_finetuned_v044@45dcc8fc"
RUN=pi0_camera_black_smoke
WRAP=probe BLACKOUT=all bash scripts/eval/run_libero.sh \
  "$RUN" 1 "$CK" 1 --policy.n_action_steps=5 \
  --env.observation_height=360 --env.observation_width=360
```

`CK` selects the checkpoint; `RUN` selects an unused output name. The entry point itself atomically rejects duplicate starts. This runs one episode per task, ten in total, batch1, five executed actions per chunk and all-black model images. It checks the entry point, not a new success-rate benchmark.

Require a zero shell exit code, then inspect `stdout.log` for `exit=0` and `out/eval_info.json` for ten episodes under `$EMB_ROOT/logs/eval/$RUN/`. Command success alone is not result acceptance. Resolve environment/checkpoint/EGL failures using [troubleshooting](../docs/TROUBLESHOOTING.md); do not overwrite old runs or blindly retry.

## State-input and replay follow-ups

| Goal | Entry | Requirements and outputs |
|---|---|---|
| Recompute completed P1/P2 | [summarize_followup.py](analysis/summarize_followup.py) | NumPy; no model/GPU; six CSVs and bilingual statistics figures |
| Repeat P1 state-input evaluation | [run_state_feedback.py](eval/run_state_feedback.py) → [eval_state_feedback.py](eval/eval_state_feedback.py) | Configured policy/EGL runtime;40 engineering+1200 formal episodes, gated stages |
| Repeat P2 frozen replay | [replay_holdout.py](analysis/replay_holdout.py) | Configured LIBERO/MuJoCo 3.3.2/EGL; at least 8/10 self-replays before 400 formal episodes; no policy |

### P1 launch steps: for an authorized independent repeat

Complete [offline preparation](../docs/INSTALL.md#41-prepare-for-offline-evaluation) for the LeRobot π0 v044 checkpoint, local tokenizer and LIBERO assets; skip the SmolVLA base-model download block. This entry uses the current Python interpreter; it does not load `env.sh` or activate conda itself. Explicitly activate `smolvla` on the Linux workstation. Set `REPO` to this checkout's absolute path and `EMB_ROOT` to the configured working directory.

**The following starts 40 engineering + 1,200 formal episodes with model/GPU inference and simulation; it was not executed during this documentation update.** Run only for an authorized repetition, not to recompute public statistics. Choose an unused prefix and isolated JOB directory; run from any directory:

```bash
(
  set -e
  source "$EMB_ROOT/env.sh"
  conda activate smolvla
  export HF_HUB_CACHE="$HF_HOME/hub"
  export STATE_RUN_PREFIX=statefb_repeat_01
  P1_JOB="$EMB_ROOT/tmp/$STATE_RUN_PREFIX"
  mkdir -- "$P1_JOB"
  cp -R -- "$REPO/scripts" "$P1_JOB/scripts"
  mkdir -p -- "$EMB_ROOT/logs/eval"
  python -u "$P1_JOB/scripts/eval/run_state_feedback.py" > "$P1_JOB/pipeline.log" 2>&1
)
```

`set -e` stops after preparation failures; the subshell leaves the current terminal's activation unchanged. `mkdir` refuses an existing JOB. Copying the complete `scripts/` tree lets the entry locate its sibling wrappers. Copy public scripts only, not weights, tokenizer or papers. The log parent is created before execution; the original entry reserves each group's output exclusively.

Expect `manifest.json`, `started.flag`, `smoke_pass.flag`, `r0_pass.flag`, `r1_pass.flag`, `r2_pass.flag` and finally `done.flag` in the JOB; require outer exit 0. The 16 runs live under `logs/eval/${STATE_RUN_PREFIX}_{smoke,r0,r1,r2}_{A,B,C,D}/`. Check each `exit_code` is 0 (this entry does not append the shell wrapper's `exit=0` to stdout), plus `out/eval_info.json`, `evidence.json`, `traj.npz` and state NPZ files. Engineering runs have 10 episodes per group; each formal group/repeat has 100. Preserve 360 rendering, five executed actions, seed=1000 and the original groups/pairing criteria.

The entry gates engineering checks, cross-condition pairing and three formal repeats; technical/evidence failure stops progression. Keep failed directories/markers. Changing `STATE_RUN_PREFIX` does not bypass the same JOB's `started.flag`; audit the cause and choose a new JOB/prefix rather than delete the marker. The workflow depends on the configured environment. Commands have static checks, not clean-machine or new model-run acceptance. Recovery experiments and P3 remain paused.

### P2 frozen-action replay

P2's ten selected action arrays are bundled in [data/replay_holdout](../dashboard/data/replay_holdout/); no OpenPI server or source-trajectory regeneration is needed. From the checkout root in the configured simulation environment, the following runs all 410 episodes, not offline analysis:

```bash
python scripts/analysis/replay_holdout.py \
  --output "$EMB_ROOT/logs/eval/p2_replay_check"
```

The output directory must not exist. Inspect `self_gate.json`, `progress.json`, `done.json` and actual errors. Technical failures stop the run; sources are not reselected. The packaged entry retains the audited P2 replay loop; loading/directory checks have synthetic validation but no new simulation run during integration. Full NPZ files stay in the new output directory and outside Git; bundled [results](../results/README.md) are not overwritten. Recovery experiments and the original five-step-delay P3 remain deferred.

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
python3 scripts/analysis/summarize_followup.py
```

Run all three from the repository root for dashboard data, earlier figures, then P1/P2 statistics; the third requires NumPy. The [results guide](../results/README.md) lists outputs; [CI](../.github/workflows/ci.yml) checks generation consistency.

## Checks, diagnostics, and historical experiments

- **Environment checks:** [torch_check.py](checks/torch_check.py), [egl_smoke.py](checks/egl_smoke.py), and [codec_check.py](checks/codec_check.py) check GPU/torch, EGL, and video decoding.
- **π0 diagnostics:** [run_pi0_full.sh](eval/run_pi0_full.sh) and [run_pi0_action_steps.sh](eval/run_pi0_action_steps.sh) cover historical smoke/full evaluations and action-chunk checks.
- **Historical fine-tuning:** [run_statedrop_pipeline.sh](train/run_statedrop_pipeline.sh) calls [run_train.sh](train/run_train.sh); [summarize_statedrop.py](analysis/summarize_statedrop.py) summarizes the results. Outcomes and corrections remain in the [notes](../docs/NOTES.md), outside the README's main findings.
