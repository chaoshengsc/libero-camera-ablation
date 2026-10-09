# Reproduction notes

English | [中文](NOTES_CN.md)

Where each reference number comes from, version requirements, the debugging history, and the detailed record of the vision-dependence experiments. Every number can be recomputed from `dashboard/data/` (see `tests/`).
Entries are kept in chronological order. A judgement that was later overturned is marked "Correction" in place; the original text is not rewritten.

## ACT (reproduced)

- Reference: not the paper, but the `eval_info.json` shipped in the HF repository `lerobot/act_aloha_sim_transfer_cube_human@ba73b276`: Transfer Cube success rate **83.0%** (500 episodes).
- This repo: **83.2%** (500 episodes, seed 1000).

## OpenVLA (reproduced)

- This repo: **86.2%** (431/500, seed 7, single-seed 95% CI ±3.0), 72–98% per task. Consistent with the reference 84.7 ± 0.9%.

- Source: the official openvla README @ `c8f03f48` (it copies the results from Appendix E of the paper, v2).
- LIBERO-Spatial **84.7 ± 0.9%**, 3 seeds × 500 episodes (10 tasks × 50 trials), A100.
- Required versions: Python 3.10.13, PyTorch 2.2.0, transformers 4.40.1, flash-attn 2.5.5; evaluate with `--center_crop True` (training used random crops of 90% area).
- MuJoCo ≥ 3.3.3 makes LIBERO render darker, so 3.3.2 is required (LIBERO issue #88, by OpenVLA's first author; in openvla issue #282 someone dropped from ~70% to 62.6% because of this and returned to 85% after downgrading).

## SmolVLA (`lerobot/smolvla_libero` reproduced; `HuggingFaceVLA/smolvla_libero` below the paper)

- This repo, `HuggingFaceVLA/smolvla_libero`: **75.2%** (500 episodes, batch_size=10); 72% when taking the first 10 trials per task as in the paper's protocol.
- Community measurements with the same checkpoint (lerobot issue #2354): Spatial 82–83%. reobf points out that this checkpoint has `expert_width_multiplier=0.5` and a 32-layer VLM,
  while the paper uses 0.75 and 16 layers, and that the checkpoint looks under-trained. **The public checkpoint itself does not reach the paper's 90%.**
- This repo is about 7 points below the community numbers, still to be explained: ~~batch_size=10~~ (control: batch_size=1 gives 75.0% over 100 episodes, **ruled out**), ~~`n_action_steps=10`~~ (**ruled out** after a control evaluation). The cause has not been found.
- Ruled out: `max_parallel_tasks=1` (the shared policy state bug of issue #4341 does not apply); fps=20; mujoco 3.3.2 (issue #4390 concerns ≥ 3.4.0).
- **Correction (2026-10-04): marking `n_action_steps=10` as "ruled out" above was wrong.** That control (`smolvla_ablB_bs1_nas10`) gave 65/100, lower than the 75/100 at `n_action_steps=1`, while the community's 82–83% was reported at `n_action_steps=10`, so the gap is larger, not smaller.
  Those community numbers are from LeRobot v0.4.x in late 2025. On v0.6.1, the version used here, lerobot issue #4614 reports 31/50 (62%) for the same checkpoint and setting, consistent with this repo. Why the versions differ was not investigated.
- Diagnosis (2026-10-03, 100 episodes each, seed 1000):
  - Render resolution: the training data is 256×256, while LeRobot's LIBERO environment renders at 360×360 by default (`envs/configs.py:333-334`). At 256×256 the result is 76/100 (72 and 75 at 360); paired by episode 12 vs 11, no effect.
  - Another checkpoint, `lerobot/smolvla_libero@31d453f7`, with `n_action_steps=10` and the camera `--rename_map`: 85/100, or 76/90 (84.4%) without task 5; in #4614 someone else gets 115/135 (85.2%) on CUDA. The evaluation stack here agrees with the community.
    Task 5 is 9/10 here: mujoco 3.3.2 does not have the init-state problem of #4390. The base model of this checkpoint is `HuggingFaceTB/SmolVLM2-500M-Video-Instruct@7b375e1b`.
- **`lerobot/smolvla_libero`, 500 episodes (2026-10-04): 85.4% (427/500, ±3.1)**, per task 45/47/45/45/34/38/49/38/42/44. Its interval overlaps that of the paper's 90% (100 episodes, about ±6), so by this repo's criterion it counts as reproduced.
  It was trained on LIBERO-Spatial only, for 25k steps, while the paper trains on all four suites, so it reaches the paper's number rather than reproducing the paper's model. The reproduction table uses this row.
- Conclusion: `HuggingFaceVLA/smolvla_libero` simply scores 65–75% on the current LeRobot version; the gap is in the checkpoint, not in this setup. The vision-dependence experiments still use that checkpoint.

Source: Table 2 of the paper and the experimental setup in the main text.

- LIBERO success rates (SmolVLA 0.45B, no robot-data pretraining): Spatial **90** / Object 96 / Goal 92 / Long 71 / average 87.3.
- Same table, for comparison: π0 (3.3B, pretrained) Spatial 90 / Object 86 / Goal 95 / Long 73 / average 86.0; OpenVLA 84.7 / 88.4 / 79.2 / 53.7.
- **Evaluation protocol: 10 trials per task, 100 episodes per suite.** The 95% confidence interval of the 90% figure is therefore about ±6 points.
- Training: dataset `physical-intelligence/libero` (1,693 episodes), multi-task over the four suites; 100k steps, batch 64.
- **`n_action_steps` matters a lot** (Table 13, average over the four suites): 1 step 80.3 / 10 steps 82.8 / 30 steps 70.8 / 50 steps 51.8.
  Chunk size in Table 12: 10 → 84.0, 50 → 80.3.
- The two public checkpoints compared (configs read from HF):
  - `HuggingFaceVLA/smolvla_libero@6721902b`: `n_action_steps=1`, input keys `image`/`image2` (the naming of physical-intelligence/libero). **Closest to the paper; this is the main reproduction target.**
    But `num_vlm_layers=0`: in the LeRobot code (`smolvlm_with_expert.py:102`) the VLM is truncated only when the value is > 0, so it **uses all layers of SmolVLM2-500M**,
    whereas the paper's main model uses only the first half (N=16, Table 8). The checkpoint is 1218 MB, larger than the 16-layer `lerobot` one (907 MB), which is consistent. Keep this in mind when comparing with the paper.
  - `lerobot/smolvla_libero@31d453f7`: `n_action_steps=50`, trained on `libero_spatial` only, 25k steps, batch 32. Different from the paper's setup; used only as a control.

## π0.5 (reproduced)

- Checkpoint `lerobot/pi05_libero_finetuned_v044@8e174154` (safetensors, not gated); the tokenizer comes from the gated repository `google/paligemma-3b-pt-224`, kept as a local copy.
- Evaluated with `--policy.n_action_steps=10` as in LeRobot's `docs/source/libero.mdx` (the documentation says this matches OpenPI).
- This repo: **98.0%** (500 episodes, 95% CI ±1.2); references: LeRobot 97.0% (10 trials per task), OpenPI 98.8%.

## Diffusion Policy (reproduced, PushT)

- The original plan was robomimic (MuJoCo), but its official legacy environment (Python 3.9 / torch 1.12 / mujoco-py 2.1 / gym 0.21) did not fit the time budget, so PushT was used instead (2D physics, not MuJoCo).
- Checkpoint `lerobot/diffusion_pusht@84a7c231` (old format, migrated locally; the migration script hits a list→tuple encoding bug, worked around with a wrapper that does not modify the source).
- This repo: **63.0%** (500 episodes, ±4.2), avg_max_reward 0.941; references: LeRobot model card 65.4%, the equivalent model in the original DP repository 64.2%.

## π0 (paper number not reproduced)

- Checkpoint `lerobot/pi0_libero_finetuned_v044@45dcc8fc`; evaluated with `--policy.n_action_steps=5`, matching `replan_steps=5` in the script used for the OpenPI reference, `examples/libero/main.py@c015073f`.
- Reference: the earlier OpenPI LIBERO README (commit c015073f), π0 fine-tuned for 30k steps, Spatial **96.8%**. Note that this is the checkpoint OpenPI trained itself, not the LeRobot one.
- This repo: **73.4%** (500 episodes, ±3.9); per task 68/86/92/84/58/64/78/80/68/56.
- Community result with the same LeRobot checkpoint (lerobot issue #2114): Spatial 69% (mujoco 2.3.7) → **73%** (mujoco 3.3.2), consistent with this repo.
- LeRobot maintainer pkooij (#2114, 2025-10-05): "The Pi0 checkpoint is finetuned but needs more training to achieve results similar to the paper." **The public checkpoint is under-trained.**
- Related evidence, #3591: with both cameras blacked out this π0 still reaches about 60% (74.6% normally), which suggests it relies little on vision (LIBERO scenes vary little, so it may be "memorising the answer" from language and proprioceptive state). Reproduced independently here; see the next section.
- Diagnosis (2026-10-03): rendering at 256×256 (matching the training data) gives 74/100; three runs at 360×360 gave 73, 76 and 76; paired by episode 11 vs 10, no effect.
- Training this checkpoint for 10k more steps (action expert only, batch 16; the control arm of the fine-tuning section below) leaves normal success at 73%.
- Not done: evaluating OpenPI's own π0 LIBERO checkpoint here to check that it reaches 97%.
- Correction (2026-10-06): the premise of the previous item is wrong. OpenPI never released a π0 LIBERO checkpoint. The 96.8% comes from an earlier README (`examples/libero/README.md@7cf5f609`), which says that training with the `pi0_libero` config should give similar results; commit `35106c9b` (2025-09) replaced that row with π0.5, and only `pi05_libero` is public. There is therefore no official π0 checkpoint to compare against. Training one here as the maintainer suggests (batch 256, 20k steps or more) is not practical: at batch 16 a step takes 4.2 s and 10k steps took 11.7 h, so a linear extrapolation gives about 15 days (an estimate, not measured). The 10k-step run above trained the action expert only, on `lerobot/libero`, which is not the maintainer's recipe, so it does not show that more training is useless.

## Vision-dependence test: all cameras blacked out (2026-09-30)

- Method: a wrapper replaces the camera images fed to the policy with black frames (for LeRobot policies it replaces `lerobot_eval.preprocess_observation`; for OpenVLA it replaces `get_libero_image`), without modifying any source;
  the recorded videos are still the real renders. Each model: LIBERO-Spatial, 10 tasks × 10 trials; the control is the first 10 trials per task of each model's 500-episode evaluation (same seed, same initial states).
- Results (normal → black): π0.5 99 → 0, OpenVLA 81 → 0, SmolVLA 72 → 0, **π0 76 → 56**.
- π0 per task when blind: 7 8 9 8 6 **1** 9 **0** 7 **1**. Only three tasks fail: bowl on the ramekin, on the stove, on top of the wooden cabinet.
- Consistent with lerobot issue #3591 (about 60% when blind); reproduced independently here. The reading at the time (to be verified): this π0 checkpoint relies heavily on language and proprioceptive state to "replay a memorised trajectory",
  which may also be one reason it falls short of the paper. The follow-up trajectory experiments and their correction are below.
- Control from the same period: π0 with `n_action_steps` 5 / 10 / 50 → 76 / 70 / 68% (100 episodes each). The differences are within error; this setting is not the main cause.

### Does π0 "replay a trajectory"? Frame-by-frame video comparison (CPU)

- Videos of the same task and episode index (same initial state), downscaled to 90×90 greyscale, aligned by time step, mean absolute difference per frame. Sanity check: frame 0 differs by 0.35/255, so episodes are aligned correctly.
- Mean difference over the episode: blind π0 vs normal π0 **6.05**; control, normal π0.5 vs normal π0, **5.22**. Blind episodes that still succeed 5.35, failed ones 6.93.
- Conclusion: **"replaying exactly the same trajectory" does not hold.** The difference between blind and sighted π0 is no smaller than the difference between two different models.
  More likely it executes an "average solution" for the task description; object positions vary little in LIBERO, which is enough for most tasks and fails on the 3 tasks with unusual bowl positions (5/7/9; difference 7.7–8.3 vs ~5 for the control).
- Correction (2026-09-30): the "average solution" guess in the previous item is contradicted by the end-effector data (grasp points do not cluster). The next section supersedes it.
- The videos are 360×360; downscaling to 90×90 is a 4×4 block average with no cropping.
- Limitation: pixel differences are aligned in time and cannot separate "different path" from "different speed". A firm conclusion needs end-effector trajectories (requires re-running on the GPU).

### End-effector trajectories (2026-09-30, 100 episodes per run, same seed and initial states)

- The wrapper `eval_probe.py` logs `robot_state.eef.pos` and the gripper opening at every step; DTW removes speed differences so only the path is compared; grasp point = end-effector position when the gripper first clearly closes.
- Path DTW / grasp-point distance: noise floor (normal π0 run twice) **2.12 / 1.51 cm**; blind π0 vs normal **4.44 / 5.03 cm**; π0.5 vs π0 (both normal) 3.28 / 2.65 cm.
- Spread of grasp points over the 10 episodes of a task: normal π0 1.78, re-run 1.79, blind 2.41 (about 1.9 without task 7), π0.5 1.56 cm.
- Conclusion: blind π0 takes a different path (twice the noise), but its grasp points do not "collapse to one spot", so the "average solution" guess does not hold either.
  More likely **LIBERO-Spatial scenes vary very little** (grasp points of a task spread by about 1.8 cm, the same order as the 1.5 cm noise between two runs of one model);
  the bowl is over ten centimetres wide, so a grasp that is off by about 5 cm still succeeds about half the time.
- Note: the other three models dropping to 0% when blacked out does not necessarily mean they "use vision to localise"; a black image is out of the training distribution and may simply disrupt the action output.
  Milder perturbations such as noise or a different scene image are needed to tell these apart.
- **Correction (2026-10-01): the conclusion above, "takes a different path (twice the noise)", does not hold.** Per task (`results/trajectory.csv`):
  - The 2.12 cm noise floor is pulled down by tasks 0–3: on these four tasks the two runs coincide almost point for point (0.04–0.30 cm) because they share a seed and have not diverged yet, which says nothing about noise. On tasks 4–9 the re-run difference is 3.4 cm (grasp point 2.4 cm).
  - The 4.44 cm for blind vs normal comes mostly from tasks 5, 7 and 9, which fail when blind (6.0 / 10.9 / 7.8 cm). On the seven tasks that still succeed it is 2.8 cm (grasp point 2.4 cm), comparable to π0.5 vs π0 at 2.9 cm (grasp point 2.6 cm) and to the re-run at 3.4 cm.
  - So: on tasks that still succeed blind, π0's path cannot be distinguished from the sighted one within noise; on tasks that fail it goes somewhere else. The grasp-point spread (blind 2.4, normal 1.8 cm) is also at noise level,
    so trajectories cannot separate "following the bowl" from "repeating one motion per task". "Scenes vary little and the benchmark asks little" still stands; "a grasp off by 5 cm still succeeds half the time" has no data behind it and is withdrawn.
  - Success rates of the three π0 runs that logged trajectories: normal 73%, normal re-run 76%, blind 54%.
- The state the policy receives is end-effector position (3) + axis-angle (3) + gripper (2), 8 dimensions in total, not joint angles (LeRobot v0.6.1 `processor/env_processor.py:68-75`, checked in the installed source).

### Blacking out one camera only (2026-10-01, 100 episodes per run; image = agent view, image2 = wrist, eye_in_hand)

| Model | Normal | Agent-view black | Wrist black | All black |
|---|---|---|---|---|
| π0 | 76 | **78** | 59 | 56 |
| π0.5 | 99 | 51 | **0** | 0 |
| SmolVLA | 72 | 2 | 5 | 0 |

- π0: blacking out the agent view has **no measurable effect** (78 vs 76, within error); 59% with the wrist camera black is on par with 56% for all black. The agent view contributes almost nothing.
- π0.5: **cannot do without the wrist camera** (0% once it is black); with the agent view black it drops to 51%. It uses both, and the wrist camera matters more.
- SmolVLA: blacking out either camera takes it to almost zero (2% / 5%). This looks more like extreme sensitivity to out-of-distribution input than proof that both cameras are used for localisation (see the note in the previous section; the frozen-first-frame result is in the "Mild perturbations" section).

### Continued fine-tuning of π0 with the state input randomly zeroed during training (2026-10-01)

- Setup: continue training from `lerobot/pi0_libero_finetuned_v044` on `lerobot/libero@a1aaacb7`; `train_expert_only` (VLM frozen, only the action expert is trained),
  bf16, gradient checkpointing, batch 16, 3000 steps (about 3.5 hours per run, peak memory 15.5 GB). That is about 15% of the original training (10k steps × batch 32).
- Two runs: control `STATE_DROP_P=0`; treatment `STATE_DROP_P=0.5` (the normalised `observation.state` is zeroed per sample, during training only).
- Training loss: control 0.145 → 0.135 (already converged); treatment, first batch **0.835** (removing the state makes the loss jump about 6×, so the original π0 depends strongly on the state input) → 0.264.
- Evaluation (LIBERO-Spatial, 100 episodes each, n_action_steps=5):

| Model | Normal | All black | Drop |
|---|---|---|---|
| Original π0 | 76 | 56 | 20 |
| Fine-tuned, control | 78 | 61 | 17 |
| Fine-tuned, state zeroing | 68 | **40** | **28** |

- All black: treatment 40% vs control 61%, a 21-point difference, z≈3.0 (two-proportion test, p≈0.003). The change significantly reduces the ability to act without looking.
- Normal: treatment 68% vs control 78%, a 10-point difference, z≈1.6 (p≈0.11). A downward trend, not significant.
- "Relies more on vision" should be judged by the extra drop caused by blacking out: control 17, treatment 28, a difference of 11 points; paired by task, t≈2.2 (9 degrees of freedom, p≈0.06), at the edge of significance.
  The 61 vs 40 under blackout includes the treatment being worse overall (normal also fell by 10 points and its loss did not converge to the control's level). Each run was trained once; there are no repeats over training seeds.
- Conclusion: the result is consistent with "state zeroing pushes π0 towards relying more on vision", but not enough to establish it; at this training budget it also brought no improvement in overall success. Training was only 15% of the original
  and the treatment's loss has not reached the control's level. Whether longer training can recover success while relying more on vision is the next question.
- **Correction (2026-10-04): the difference seen at 3000 steps did not replicate with longer training.** Same setup, 10k steps per arm (warmup 1000, checkpoint every 5000), each checkpoint evaluated for 100 normal and 100 blind episodes:

| Steps | Arm | Normal | All black | Drop |
|---|---|---|---|---|
| 5000 | control | 72 | 53 | 19 |
| 5000 | state zeroing | 69 | 55 | 14 |
| 10000 | control | 73 | 51 | 22 |
| 10000 | state zeroing | 74 | 52 | 22 |

  At 10k steps the two arms do not differ in normal success, blind success or the drop; at 5000 steps the direction is reversed and within noise. The treatment's training loss ends at about 0.26–0.29, the control's at about 0.14.
  The 61 vs 40 at 3000 steps came from a single training run and was more likely chance or a transient of early training; "state zeroing makes π0 rely more on vision" is not supported, and the README no longer includes this experiment.
  Raw files: `dashboard/data/eval_ft10k_*`. Lesson: a single-run difference at p≈0.06 should not have been written up as a finding.

### Mild perturbations: noise / frozen image (2026-10-01, 100 episodes per run, same seed and initial states)

- Implementation: image noise is added to the CPU tensor before it reaches the policy (after `lerobot_eval.py:274`), while the policy's own sampling noise is generated on the GPU (`policies/common/flow_matching.py:43-51`).
  They use different random streams, so adding image noise does not change the policy's sampling noise sequence (checked in the installed LeRobot v0.6.1 source).
- Motivation: a black image is out of the training distribution, so three models dropping to 0% does not necessarily mean they "use vision to localise"; they may simply be disrupted by out-of-distribution input. Two milder perturbations separate these:
  Gaussian noise (standard deviation 0.1, image content preserved) and a frozen first frame (a real, in-distribution image that is never updated during the episode).
- Results (successes / 100, normal → noise → frozen first frame → all black): π0 76 → 79 → 71 → 56; π0.5 99 → 99 → 0 → 0; SmolVLA 72 → 32 → 0 → 0.
- Conclusion: π0.5 is insensitive to noise but drops to zero as soon as the image freezes. It really does use the live image in closed loop, and its 0% under blackout is not an out-of-distribution artefact.
  π0 loses only 5 points with a frozen first frame (within error), so it barely needs live visual feedback.
  SmolVLA is also at 0% with a frozen first frame (0 on all 10 tasks): the frozen frame is a real in-distribution image, so like π0.5 it needs a live image, and "just sensitive to out-of-distribution input" cannot explain this cell;
  dropping to 32% under noise shows it is sensitive to image quality as well.

### Correction (2026-10-07): SmolVLA re-run with `lerobot/smolvla_libero`; the "benchmark asks little" claim is withdrawn

- **SmolVLA checkpoint changed.** SmolVLA in the sections above is `HuggingFaceVLA/smolvla_libero` (75.2% over 500 episodes), while the reproduction table uses `lerobot/smolvla_libero` (85.4%). To use one SmolVLA checkpoint throughout, the five camera conditions were re-run with the latter (100 episodes each, same seed and initial states, `n_action_steps=10` plus `rename_map`). The wrappers act before the renaming: the logs show the image keys are still `image` / `image2`, and their maximum is 0 after blackout.

  | Checkpoint | Normal | Noise | Frozen first frame | Agent-view black | Wrist black | All black |
  |---|---|---|---|---|---|---|
  | `HuggingFaceVLA/smolvla_libero` (old) | 72 | 32 | 0 | 2 | 5 | 0 |
  | `lerobot/smolvla_libero` (new, used in the README) | 83 | 78 | 0 | 33 | 4 | 0 |

  Unchanged: a frozen first frame and black cameras both give 0, and the wrist camera matters more than the agent view. Changed: "SmolVLA is sensitive to image quality (32% with noise)" holds for the old checkpoint only; the new one scores 78% with noise, within error of its normal 83%. With the agent view black the old checkpoint is near 0 and the new one still reaches 33%. The old checkpoint's evaluation files remain in `dashboard/data/` (`smolvla_hfvla_500`, `smolvla_black_all`, `pert_smol_*`).
- **Raw data for OpenVLA with black cameras added.** The workstation log from 2026-09-30 was converted to `dashboard/data/openvla_black_all/eval_info.json` (0/100), and the tests now check all 8 rows of the blackout table.
- **"The scene varies little, the benchmark asks little" is withdrawn.** It rested on sighted π0's grasp point spreading only 1.8 cm within a task. This π0 barely depends on images to begin with, so a small spread may be its own behaviour and cannot show that the bowl position varies little. How much the bowl position varies between initial states of a task was not measured in this project. The corresponding sentences were removed from the README and the dashboard. Related public work: LIBERO-PRO (arXiv:2510.03827) and LIBERO-Plus (arXiv:2510.13626); only the abstracts were read.
- **The repository was renamed** to `libero-camera-ablation`, and the README now puts the ablations first and the reproduction second.
- **The claim about task 5 is narrowed.** The earlier text said that on the three tasks blind π0 fails (5, 7, 9) the path differs by 6 to 11 cm and it goes somewhere else. On task 5 the 6.0 cm is no larger than the 6.6 cm between two sighted runs on that task, so the statement holds only for task 7 (10.9 vs. 2.6) and task 9 (7.8 vs. 3.3); task 5 is inconclusive. The README and the dashboard were changed.

### Correction (2026-10-07, evening): after a full re-run, "π0 depends on the wrist camera" is withdrawn

The three pipelines were re-run end to end on the workstation with the scripts as they are in the repository (`run_blackout_all.sh`, `run_perturbation.sh`, `run_trajectory_and_single_camera.sh`; 20 evaluations, 100 episodes each, same seed). The raw data of the second run is in `dashboard/data/run2/`.

- **Script problem.** `run_blackout_all.sh` used to run OpenVLA alongside π0.5, and OpenVLA ran out of GPU memory while loading (OpenVLA about 14 GB, π0.5 about 9.4 GB, 24 GB card). OpenVLA now runs alone after the other three models. The re-run passed and OpenVLA is again 0/100 (log on the workstation, not converted into the repository).
- **Successes in the two runs (first / second).**

  | Model | Normal | Noise | Frozen first frame | Agent-view black | Wrist black | All black |
  |---|---|---|---|---|---|---|
  | π0 | 76 / 72 | 79 / 67 | 71 / 80 | 78 / 68 | 59 / 77 | 56 / 56 |
  | π0.5 | 99 / 98 | 99 / 97 | 0 / 0 | 51 / 57 | 0 / 0 | 0 / 0 |
  | SmolVLA | 83 / – | 78 / 73 | 0 / 0 | 33 / 31 | 4 / 4 | 0 / 0 |

  π0 with all cameras black, five runs: 56, 54, 56, 54, 53 (the last from one more re-run after the script fix, data in `dashboard/data/run3/`). π0 normal, five runs: 76, 73, 76, 72, 71.
- **Withdrawn.** "Losing the wrist camera (59%) costs about as much as losing both (56%), so π0 does use the wrist image": the second wrist-black run gave 77% and did not repeat it. "The wrist camera matters more than the agent view for all three models" is narrowed to π0.5 and SmolVLA.
- **Unchanged.** π0 with black cameras stays at 53–56%. π0.5 and SmolVLA score 0 without a live image. π0.5 and SmolVLA repeat within 6 points.
- **Added.** Two runs with the same seed are not identical. π0 differed by up to 18 points on one condition, more than the roughly 13 points expected from binomial sampling. The cause was not investigated. The README table and figure now show both runs.
- **Not done.** The trajectory comparison in section 1.3 still uses the trajectories of the first run only.

## Correction (2026-10-09): section 1.3 recomputed on the second run

The trajectory comparison in section 1.3 was based on one run. The same analysis was repeated on the trajectories of the second run (`dashboard/data/run2/traj_analyze.json`; both runs are in `results/trajectory.csv`).

- **Holds in both runs.** On the tasks blind π0 solves at least half the time, its path differs from the sighted path by 2.8 and 3.2 cm (grasp point 2.4 and 2.2 cm); two sighted runs differ by 3.4 and 3.3 cm. On task 7 blind π0 never succeeds and ends up elsewhere: 10.9 and 10.3 cm, grasp point 24.1 and 23.7 cm.
- **Weakened: task 9.** The first run gave 7.8 cm against 3.3 cm between sighted runs. The second gives 4.9 against 3.6 cm, and blind π0 succeeded once. The README no longer lists task 9 next to task 7.
- **Changed wording.** "Re-runs of tasks 0–3 are almost identical" is true of the first run only. In the second run tasks 1–3 had already diverged (2.3 to 3.1 cm), although the seed is the same. The noise floor now uses every task where the two sighted runs differ by more than 1 cm.
- **The set of solved tasks is not fixed.** Task 8 was solved 5 times out of 10 in the first run and 4 in the second, so the first row of the table covers seven tasks in one run and six in the other.
