# Continuing camera experiments on another device requires runtime preparation

[中文](CONTINUE_CN.md) · [Project overview](../README.md) · [Installation](INSTALL.md)

The repository provides public outcomes, evaluation code, recorded settings and installation instructions. New model evaluations additionally need a selected runtime, checkpoints, tokenizers and simulation assets. The reference path is the existing Ubuntu 24.04/NVIDIA setup; no clean target device has passed installation-through-rollout acceptance. Full simulation on Windows or macOS is unverified.

## Different goals require different materials

| Goal | Required materials | Current status |
|---|---|---|
| Recompute published statistics and figures | Repository, Python 3.10+, NumPy | Public records are available; no model or GPU; see [quick start](../README.md#quick-start) |
| Run new camera evaluations | Fixed sources, selected environment, checkpoint/processors, LIBERO tasks/initial states/assets, new normal control and unused outputs | Code and preparation instructions are public; target-device preparation and runtime acceptance remain pending |
| Repeat full historical behavioral audits | Original NPZ, logs, recordings and audit inputs | Full artifacts remain outside Git; never-saved image/termination fields cannot be recovered |

Old full NPZ files are not prerequisites for new camera experiments. Outcome JSON files do not replace checkpoint or simulator assets.

## Runtime assets are prepared separately for each path

| Path | Required inputs | Preparation |
|---|---|---|
| LeRobot π0/π0.5 | Corresponding v044 checkpoint, normalization/preprocessing files and authorized PaliGemma tokenizer; update local tokenizer paths on the target device | [Install](INSTALL.md); the selected environment suffices, without ACT/DP or training data |
| SmolVLA | Policy checkpoint, fixed SmolVLM2 backbone/processor cache and camera rename mapping | [Offline preparation](INSTALL.md#41-prepare-for-offline-evaluation) · [Script parameters](../scripts/README.md#public-checkpoint-reproduction) |
| OpenVLA | Separate Python environment, fixed OpenVLA/original LIBERO sources, checkpoint, tasks/initial states/assets | [Installation](INSTALL.md) |
| Official π0/OpenPI | Separate JAX environment, native Orbax checkpoint, norm_stats, GCS tokenizer cache and configuration-only client | [OpenPI guide](OPENPI.md); the failed HF candidate is not a replacement for native weights |
| P2 fixed-action replay | Simulator, tasks/initial states/assets and published frozen actions/selection | [Replay inputs](../dashboard/data/replay_holdout/README.md); no policy model is called |

Fixed source and checkpoint revisions are documented in [installation](INSTALL.md), [common settings](../scripts/common.sh) and the [run manifest](../configs/camera_study_runs.json). Weights, gated tokenizers and credentials stay outside Git. Native GCS prefixes can change: identical names do not establish identical weights; retain and compare the original download listing or independently preserved content hashes.

LIBERO requires BDDL tasks, `.pruned_init` states and mesh/texture assets. The guide pins a snapshot for future installation, not the complete historical assets revision. Preserve old tasks/states/assets and their inventories separately if closer historical matching is needed. Evaluation does not require demonstration training data. [Asset preparation](INSTALL.md) checks default layouts and file presence, not custom configuration, full content hashes or rendering acceptance.

Environment exports are [examples and historical inventories](../env/README.md), not accepted installations portable across operating systems. The three old conda exports do not include the separate OpenPI environment. Historical `eval_ft*` and training scripts remain as earlier diagnostics; they are outside the separate current fine-tuning project and the camera-evidence manifest.

## Eleven historical runs have an explicit settings index

The [JSON manifest](../configs/camera_study_runs.json) separates recorded history, future recipes and unstarted plans. Each historical run has ten tasks × 50 states, batch one, entry seed 1000, predicted chunk 50, ten internal iterations and budget 280. π0 executes five actions before replanning; π0.5 executes ten. Per-run evidence is in [provenance](../dashboard/data/protocol_audit/provenance.json).

| Historical run | Intervention | Public-analysis normal reference |
|---|---|---|
| `s500/pi05_none` | Normal | `s500/pi05_none` |
| `s500/pi05_drop_wrist` | Wrist mask | `s500/pi05_none` |
| `s500/pi05_freeze_wrist` | Wrist first frame | `s500/pi05_none` |
| `s500/pi05_drop_agent` | Agent mask | `s500/pi05_none` |
| `s500/pi0_none` | Normal | `s500/pi0_none` |
| `s500/pi0_none_r2` | Normal | `s500/pi0_none` |
| `s500/pi0_wrist` | Wrist black | `s500/pi0_none` |
| `s500/pi0_drop_wrist` | Wrist mask | `s500/pi0_none` |
| `s500/pi0_drop_wrist_r2` | Wrist mask | `s500/pi0_none` |
| `s500/pi0_freeze_wrist` | Wrist first frame | `s500/pi0_none` |
| `s500/pi0_drop_agent` | Agent mask | `s500/pi0_none` |

These normal references follow the public analysis. An `r2` suffix does not establish contemporaneous pairing. Historical exports explicitly record height 360 but omit width, represented by null in the manifest. Future recipes explicitly select 360×360 and budget 280; they do not reconstruct an otherwise unrecorded historical CLI.

π0.5 wrist black instead uses five historical executions of the same 100 initial states; it is not one of these eleven new 500-state runs. Matching task/start indices and first-frame hashes does not establish bitwise-matched complete states or policy noise.

## The command helper only prints one selected recipe

From the checkout root, use Python 3.10+ without third-party packages. These commands list templates or print a command: they never execute it, load models or create run outputs.

```bash
python scripts/eval/camera_study_commands.py --list
python scripts/eval/camera_study_commands.py   --run s500/pi05_drop_wrist --new-run-name pi05_wrist_mask_new_01   --emb-root /path/to/new/workdir --smoke
```

The second command prints a one-episode-per-task, ten-episode engineering check. After target-device acceptance below, omitting `--smoke` prints a 50-per-task, 500-episode recipe. Both modes only print; inspect the command before executing it separately. The printed command clears inherited `POLICY_SERVER` and `OPENPI_AUTHKEY` and sets `DELTA_REF=chunk` to avoid switching to an OpenPI bridge or inherited diagnostics. Paths and checkpoints use the target device's `EMB_ROOT`; output names must be unused.

Generate a new normal control with `s500/pi05_none` before choosing an intervention, using separate new names and recording their pairing. Use the corresponding `pi0_*` templates for π0. Historical normal results are not automatically paired controls for a new device. Agent-only freezing, main-scale agent blackout and π0.5 both-mask remain [planned work](STUDY_MAP.md#follow-up-work-will-complete-the-remaining-applicable-controls); the manifest never starts them.

## Target-device acceptance proceeds in stages

| Stage | Acceptance evidence | Current status |
|---|---|---|
| Repository checks | Fixed Git commit, [207-file evidence check](../scripts/checks/freeze_check.py), settings consistent with public sources | Repository checks are available |
| Local preparation | Selected source/package versions, checkpoint/processors, effective cache paths, tasks/states/assets and unused outputs | Pending device selection |
| Runtime engineering check | Normal/intervention each ten episodes, exit zero, all ten tasks, finite actions, effective intervention and start matching | No new-device acceptance yet |
| Formal experiment | Predeclared controls, intervention, tasks/states, seeds, denominator, stop conditions and complete new records | Not started on a new device; to be scoped separately |

`torch_check.py` performs CUDA work; `egl_smoke.py` simulates ALOHA and writes an image; `codec_check.py` writes temporary video. They are not read-only LIBERO checks. GPU, rendering, inference and closed-loop acceptance need separate target-device records. A ten-episode engineering pass is not full success-rate reproduction.

Retain actual commands/environment variables, source/package versions, checkpoint revision/processors, asset/state inventories, task/start indices, normal-control mapping, exit status, per-episode success, first-frame matching evidence and run artifacts. Keep failed outputs and use a fresh run name for diagnosis. See the [script index](../scripts/README.md#existing-data-analysis-and-figures) for result registration and regeneration.

The current probe stores first-frame hashes in the `h0` array of `traj.npz`; it does not automatically export `first_frame_hash.json`, stepwise terminal flags or a unique stop reason. Behavioral audits requiring these fields need recording changes and acceptance first; the current command cannot establish a unique termination cause for every episode.

[Result integration](../scripts/README.md#existing-data-analysis-and-figures) separates historical regeneration from registering a new study. Record new normal/intervention mappings and initial-state matching, use separate outputs, and preserve frozen mappings. A new success rate alone is insufficient.

Installation examples have not been fully validated with spaces in working paths; use an `EMB_ROOT` without spaces for initial installation. Quoting checks in the command helper and environment template do not establish third-party installer acceptance.
