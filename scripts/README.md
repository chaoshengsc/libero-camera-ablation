# Script index

English | [中文](README_CN.md)

Every entry script first runs `source scripts/common.sh`, which loads `$EMB_ROOT/env.sh` and defines the local paths of the public checkpoints (`CK_PI0` and so on).
The wrappers (`eval_*.py`, `train_statedrop.py`, `migrate_tuplefix.py`) all replace functions at run time and do not modify the LeRobot / OpenVLA sources.

| Result | Entry point | Summary |
|---|---|---|
| ACT, 500 episodes | `eval/run_act.sh` | `analysis/summarize_eval.py` |
| Diffusion Policy on PushT, 500 episodes | `eval/run_dp_pusht.sh` | `analysis/summarize_eval.py` |
| OpenVLA on LIBERO-Spatial | `eval/run_ovla.sh <run> 50` | `analysis/ovla_to_json.py` |
| SmolVLA / π0 / π0.5 on LIBERO-Spatial | `eval/run_libero.sh <run> 50 <checkpoint dir> 1 [...]` | `analysis/summarize_eval.py` |
| π0 smoke test + full evaluation | `eval/run_pi0_full.sh` | |
| π0 `n_action_steps` | `eval/run_pi0_action_steps.sh` | `analysis/summarize_eval.py` |
| All cameras black, four models | `eval/run_blackout_all.sh` | `analysis/summarize_blackout.py` |
| Frame-by-frame video comparison | | `analysis/compare_videos.py` |
| End-effector trajectories, single camera black | `eval/run_trajectory_and_single_camera.sh` | `analysis/analyze_trajectories.py`, `analysis/summarize_single_camera.py` |
| Mild perturbations: noise, frozen image | `eval/run_perturbation.sh` | `dashboard/build.py` |
| Continued fine-tuning with state zeroing | `train/run_statedrop_pipeline.sh [steps, default 3000]` (calls `train/run_train.sh`) | `analysis/summarize_statedrop.py` |
| Data for the trajectory figure | | `analysis/export_trajectories.py 4 7` |
| README figures and `results/*.csv` | | `analysis/make_figures.py` |

The `WRAP` switch of `eval/run_libero.sh`:

| `WRAP` | What runs | Extra environment variable |
|---|---|---|
| `none` (default) | `lerobot-eval` | |
| `blackout` | `eval/eval_blackout.py` | `BLACKOUT=all\|agent\|wrist` (any other value is an error) |
| `probe` | `eval/eval_probe.py`, trajectories saved to `<output dir>/traj.npz` | `BLACKOUT=none\|all\|agent\|wrist\|noise\|freeze` |

`lerobot/smolvla_libero` (the SmolVLA row of the reproduction table) needs two extra arguments: `--policy.n_action_steps=10` and `--rename_map='{"observation.images.image": "observation.images.camera1", "observation.images.image2": "observation.images.camera2"}'`. Its base model `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` has to be in the Hugging Face cache.

Entry scripts can be called from any directory, by relative or absolute path. With a positional argument missing they print the usage and exit without touching existing results.

To bring a new evaluation into the dashboard and figures, put the `eval_info.json` from its output directory under `dashboard/data/<run>/`, then run `python3 dashboard/build.py && python3 scripts/analysis/make_figures.py`.

The three scripts under `checks/` verify a fresh environment: GPU and torch, headless EGL rendering, video decoding.

`analysis/metrics.py` holds the metrics shared by the analysis scripts (confidence interval, two-proportion z-test, DTW, grasp point) and has unit tests (`tests/`).
