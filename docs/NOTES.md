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
- Related evidence, #3591: with both cameras blacked out this π0 still reaches about 60% (74.6% normally), which suggests it relies little on vision (LIBERO scenes vary little *[withdrawn on 2026-10-07, see the correction below]*, so it may be "memorising the answer" from language and proprioceptive state). Reproduced independently here; see the next section.
- Diagnosis (2026-10-03): rendering at 256×256 (matching the training data) gives 74/100; three runs at 360×360 gave 73, 76 and 76; paired by episode 11 vs 10, no effect.
- Training this checkpoint for 10k more steps (action expert only, batch 16; the control arm of the fine-tuning section below) leaves normal success at 73%.
- Not done: evaluating OpenPI's own π0 LIBERO checkpoint here to check that it reaches 97%.
- Correction (2026-10-06): the premise of the previous item is wrong. OpenPI never released a π0 LIBERO checkpoint. *[This correction is itself wrong; see the correction of 2026-10-28 at the end.]* The 96.8% comes from an earlier README (`examples/libero/README.md@7cf5f609`), which says that training with the `pi0_libero` config should give similar results; commit `35106c9b` (2025-09) replaced that row with π0.5, and only `pi05_libero` is public. There is therefore no official π0 checkpoint to compare against. Training one here as the maintainer suggests (batch 256, 20k steps or more) is not practical: at batch 16 a step takes 4.2 s and 10k steps took 11.7 h, so a linear extrapolation gives about 15 days (an estimate, not measured). The 10k-step run above trained the action expert only, on `lerobot/libero`, which is not the maintainer's recipe, so it does not show that more training is useless.

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
    so trajectories cannot separate "following the bowl" from "repeating one motion per task". "Scenes vary little and the benchmark asks little" still stands *(Withdrawn on 2026-10-07; see the correction below.)*; "a grasp off by 5 cm still succeeds half the time" has no data behind it and is withdrawn.
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

## Why two π0 runs with the same seed differ (2026-10-09)

- **Source.** `lerobot_eval.py` (v0.6.1, lines 746–748) calls `set_seed`, and also sets `cudnn.benchmark = True` and `allow_tf32 = True`. It does not enable deterministic algorithms, so a fixed seed does not make the GPU computation bit-reproducible.
- **Checked on our data.** Four π0 normal runs share the seed and the initial states. In every one of the 100 episodes the end-effector position already differs after the first step. In most episodes the paths are more than 1 cm apart within about five steps; in a few they stay within 1 mm for 50 to 250 steps. A repeat is therefore a new sample, not a replay.
- **Wrist camera black, five runs: 59, 77, 72, 67, 70** (average 69; five normal runs average 74). The 18-point gap was the lowest and the highest of the five. Three runs were added today with the same script (`dashboard/data/run3..5/traj_pi0_wrist`).
- **Not established.** Which component introduces the first difference (cuDNN algorithm choice, TF32, bfloat16 weights, or EGL rendering) was not isolated, and no run with deterministic algorithms was made. The five wrist-black runs spread more (standard deviation 6.7) than the five normal runs (2.3) or the five all-black runs (1.3); five runs are too few to say whether that is real.

## Pre-registration: π0 / π0.5 with one camera (written 2026-10-27, before the results; translated 2026-10-28)

This is a condensed translation of the final design. The Chinese original in [NOTES_CN.md](NOTES_CN.md) keeps the timeline: the first version, an update at 21:56 and the adjustments at 22:15, all before the results; the first version dropped a camera by removing its key from the input.

- **Question.** With only the agent view, can π0 and π0.5 still do the tasks? The earlier wrist-black condition blacks out the whole wrist frame, and the model still attends to a black image it never saw in training, so π0.5's 0% cannot separate "needs the wrist view" from "is confused by a black image".
- **Design.** One main variable: how the wrist camera is treated, at four levels: normal; black (pixels 0, mask 1); dropped (handled like an empty camera: filled with -1, mask 0, in its own slot); frozen at the episode's first frame (real image, mask 1, never updated). The agent view is always normal. One extra condition: agent view dropped, wrist only. π0 and π0.5 each run these 5 conditions, 500 episodes each (10 tasks × 50 initial states, seed 1000, batch_size 1), on the same initial states as the earlier 500-episode normal runs. "Both cameras" is rerun under the same wrapper to compare with the 2026-09-30 run. π0.5 uses `n_action_steps=10`, π0 uses 5, as before.
- **Acceptance (no results reported otherwise).** Each run: the dropped camera's mask is 0 and the kept one's is 1 in the log; 500 episodes; exit code 0. Frozen runs print, at step 20 of episode 1, the difference between the image sent and frame 1: 0 for the frozen camera, above 0 for the other. Each episode records a hash of its first agent-view frame to check that runs share the initial states.
- **Adjustments after a design review (still before the results).** π0.5 wrist-black is not rerun at 500: it already has 5 × 100 episodes, 0/500 in total; the time goes to a second π0 run of "both cameras" and "wrist dropped". "Dropped" masks the camera in its own slot inside the model, because removing the key shifts the other cameras (see the finding below).
- **Statistics.** Success rate with Wilson 95% intervals; paired comparison with "both cameras" on the same initial states using McNemar's exact test, with the both-vs-rerun disagreement as the baseline; for π0 an equivalence margin of ±8 percentage points with the 95% interval of the difference. If this run's "both cameras" differs from the September run by more than 2 standard errors, each condition is run several times. Per-task results are exploratory.
- **Reading.** All three treatments (black, dropped, frozen) low → depends on the live wrist image; only black low while dropped and frozen are not → the earlier 0% came from the black image; frozen not low but dropped low → depends on having a wrist image, not on its content. Each treatment has a side effect: black is out-of-distribution pixels, dropping changes the token layout, freezing gives a stale image.
- **Expectation.** π0.5 with the agent view only near 0%; π0 with the agent view only within run-to-run variation of both cameras.
- **Wording.** "A model trained with two cameras, with the wrist camera removed at test time", not "a single-camera policy"; the conclusions apply only to these two checkpoints and LIBERO-Spatial.

## Finding: LeRobot's π0 / π0.5 / SmolVLA shift the remaining cameras when one is missing (2026-10-27)

- **What happens.** When a camera is absent from the input, these three policies place the present cameras first, in config order, and append blank images (filled with -1, attention mask 0) for the missing ones. If the missing camera is not the last one, for example the agent view, the later camera (the wrist view) moves forward into its slot. The model tells cameras apart by slot position, so it processes the wrist image as if it were the agent view, with no error or warning.
- **Source (LeRobot v0.6.1, the version installed on the workstation, checked).** `src/lerobot/policies/pi0/modeling_pi0.py` splits present and missing keys at lines 995–996, processes present ones from line 1004 and appends blanks from line 1040; `pi05/modeling_pi05.py` lines 964–965, 974, 1010; `smolvla/modeling_smolvla.py` lines 340–341, 348, 373.
- **How it was found.** A trial run with the agent view removed logged each slot's pixel range: slot 1 (agent view) had the range of the wrist image and slot 2 was blank.
- **Consequence.** Dropping an image key to ablate a camera, or to simulate a sensor dropout, is only correct when the dropped camera is the last one; otherwise it measures a camera shift rather than a missing camera. The same shift would happen on a real robot if one camera stream stops.
- **What this project does.** It does not remove the key. It masks the camera in its own slot on the output of `_preprocess_images` (`drop_*` modes in `scripts/eval/eval_probe.py`) and logs each slot's mask and pixel range as evidence.
- **Reported.** No existing issue covered this; filed as [lerobot issue #5118](https://github.com/huggingface/lerobot/issues/5118) with a minimal CPU repro. A fix for the six affected policies was opened as [lerobot PR #5129](https://github.com/huggingface/lerobot/pull/5129) on 2026-10-28 (under review at the time of writing).
- **Not done.** Other versions were not checked.

## Results: π0 / π0.5 with one camera (2026-10-28, per the pre-registration above)

- **Acceptance.** All 11 runs pass: dropped camera mask 0, kept camera mask 1; 500 episodes and exit code 0 each; in both freeze checks the frozen camera's difference is 0 and the other's is above 0 (0.64, 0.79); every run's first-frame hashes match the same model's "both cameras" run episode by episode (500/500).
- **Run-to-run.** "Both cameras" this time: π0.5 98.4% (September 98.0%); π0 72.0% (September 73.4%), a 1.4-point gap. One 500-episode run has a standard error of about 2.0 points and the difference of two runs about 2.8 points, so the gap is under one standard error and conditions were not run several times. π0's two "both cameras" runs (this one and the rerun) disagree on 162/500 initial states; this is the baseline for the paired comparisons below.

Success rate (%), 500 episodes each, Wilson 95% interval in brackets; the difference is paired by initial state against the same model's "both cameras", ± is the 95% interval, p is McNemar's exact test.

| Wrist camera | π0.5 | π0 |
|---|---|---|
| Both cameras | 98.4 (96.9–99.2) | 72.0 (67.9–75.8); rerun 71.2, diff −0.8 ± 5.0, p = 0.81 |
| Black | 0/500 (the same 100 initial states run 5 times, see below) | 70.4 (66.3–74.2), diff −1.6 ± 4.9, p = 0.58 |
| Dropped | 4.6 (3.1–6.8), diff −93.8 ± 2.2, p < 1e-60 | 71.2 (67.1–75.0), diff −0.8 ± 5.3, p = 0.82; second run 72.6, diff +0.6 ± 5.2 |
| Frozen at frame 1 | 0.0 (0.0–0.8), diff −98.4 ± 1.1, p < 1e-60 | 72.8 (68.7–76.5), diff +0.8 ± 5.1, p = 0.82 |
| Extra: agent view dropped | 55.4 (51.0–59.7), diff −43.0 ± 4.3, p < 1e-60 | 74.2 (70.2–77.8), diff +2.2 ± 4.8, p = 0.42 |

- **π0.5: as expected.** Black, dropped and frozen are all near 0. By the reading written beforehand, π0.5 depends on the live content of the wrist image, and the earlier 0% for wrist-black was not caused by the black image itself. Frozen (a real but stale image) gives 0%, lower than dropped (4.6%).
- **π0: as expected.** All three differences fall within the pre-set ±8-point margin; with the agent view only, π0 does as well as with both cameras. But π0 also reaches 56% with both cameras black (earlier 2 × 100 episodes): a large share of its successes does not depend on the images. So the result is "removing the wrist camera does not change π0's success rate", not "the agent view is enough for π0".
- **Extra condition.** With the wrist view only, π0.5 reaches 55.4%, consistent with the two earlier agent-black runs (51%, 57%). Per task (exploratory): task 5 is 1/50, task 7 is 2/50, task 2 is 49/50. π0 with the wrist view only reaches 74.2%, on par with both cameras.
- **π0.5 wrist-black runs.** The two runs of section 1.2 (`dashboard/data/traj_pi05_wrist`, `run2/traj_pi05_wrist`) plus three more run on 2026-10-27 with the same script and seed (`run3..5/traj_pi05_wrist`), 100 episodes each, all 0/100. All five use the same 100 initial states (10 per task), so they are repeats, not 500 different initial states.
- **Scope.** These two checkpoints on LIBERO-Spatial only; a model trained with two cameras with one removed at test time, not a policy trained on one camera.
- **Raw data.** Each run's `eval_info.json` and first-frame hashes are in `dashboard/data/s500/`; `scripts/analysis/make_figures.py` derives `results/single_camera.csv` (per episode) and `results/single_camera_summary.csv` (the statistics in the table above) from them.
- **Note.** The pre-registration was written before the results but was not committed before them; its timing rests on the dates in the text.

## Correction (2026-10-28): an official π0 LIBERO checkpoint does exist

The correction of 2026-10-06 above says that OpenPI never released a π0 LIBERO checkpoint. That is wrong. It was based only on OpenPI's README, and none of the 22 versions of the README lists one, but OpenPI's public bucket holds `gs://openpi-assets/checkpoints/pi0_libero` (uploaded 2025-05-28, checked through the bucket listing), next to `pi0_fast_libero` and `pi05_libero`. `pi0_libero` is also a config in `src/openpi/training/config.py`.

- [LIBERO-Plus](https://arxiv.org/abs/2510.13626) evaluated this checkpoint (their Table 6 lists the address): 94.2% unperturbed (Table 1), and at most 2% with every camera black (Figure 2, which does not say which suite). It has not been re-run here.
- So "π0 still succeeds with black cameras" is very likely a property of LeRobot's under-trained checkpoint and not of π0. The README and the dashboard said "there is no official π0 LIBERO checkpoint to compare against"; that sentence is replaced.
- Next: evaluate OpenPI's `pi0_libero` and `pi05_libero` here with every camera black and with the wrist camera removed.

## Pre-registration: does the official π0 succeed without vision? (written 2026-10-28 15:00, before the results; translated the same day)

A translation of the Chinese original in [NOTES_CN.md](NOTES_CN.md).

- **Question.** LeRobot's π0 (`lerobot/pi0_libero_finetuned_v044`) still reaches 53–56% with both cameras black (five runs). Is that a property of π0 or of this checkpoint? Method: swap in the LeRobot conversion of OpenPI's official `pi0_libero`, `lerobot/pi0_libero_base@98ac51b8` (sha256 of `model.safetensors` checked against the HF record), with the same environment, seed (1000), suite (LIBERO-Spatial) and initial states. Only the weights change.
- **How much it matters.** The README headline says "a public π0 checkpoint", which holds whatever the result; this experiment only makes the scope of the conclusion precise.
- **Running the conversion faithfully (all checked in the source).** The converted repository has no normalization statistics; OpenPI's official `norm_stats.json` is injected (mean/std; first 8 state dims, first 7 action dims). `pi0_libero` was trained with `extra_delta_transform`: the first 6 action dims are deltas from the state, so after unnormalization the first 6 dims of the raw (unnormalized) state are added back; the gripper is unchanged. Each inference executes 5 steps (as OpenPI's LIBERO script with `replan_steps=5` and the earlier LeRobot π0 runs; the converted config defaults to 10 and is set to 5). The tokenizer points to the local copy on the workstation. The environment side (180° image rotation, 8-dim state, initial wait steps) is kept as in the earlier LeRobot π0 runs.
- **Conditions and episodes.**

| Checkpoint | Normal | All black | Both slots masked | Both frozen at frame 1 (auxiliary) |
|---|---|---|---|---|
| Official π0 | 500 (gate) | 100 | 100 | 100 |
| LeRobot π0 | existing 5 × 100, 500 | existing 5 × 100 | new 100 | existing 2 × 100 |

  "Both slots masked" is a new mode: both cameras are handled as empty cameras in their own slots (filled with -1, mask 0), the same method as `drop_wrist` / `drop_agent`. 100 episodes = 10 tasks × 10 initial states; 500 = 10 tasks × 50.
- **Smoke test (not reported).** Before the gate, 50 normal episodes. The log must show: normalized state of order 1; actions after unnormalization and delta restoration within [-1, 1]; the delta actually added back (actions printed before and after). If not, fix before the gate.
- **Gate.** Official π0, normal, 500 episodes ≥ 92% (references: 96.8% on Spatial in OpenPI's old README for this config; 94.2% reported by LIBERO-Plus). Below that, stop, report no ablation results, and check normalization, delta restoration and executed steps; if needed, switch to OpenPI's original JAX implementation.
- **Acceptance per run (not reported otherwise).** Exit code 0; right number of episodes; in masked runs every image slot's mask is 0 in the log; each episode records a hash of its first agent-view frame, compared episode by episode with the existing LeRobot π0 500-episode normal run (`dashboard/data/s500/`; 100-episode runs against the first 10 per task), to confirm the same initial states.
- **Reading (only all-black and both-slots-masked, the two treatments that actually remove visual information).**
  - Official π0 ≤ 10% under both, and LeRobot π0 ≥ 40% under the matching treatment → confirmed as a property of this checkpoint; "very likely" in the README becomes a definite statement. If LeRobot π0 with both slots masked is below 40%, this rests on all-black alone, and that is stated.
  - Official π0 ≥ 30% under either → reported as is for that treatment, and the general "property of this checkpoint" claim is withdrawn.
  - 10–30% → that treatment is run once more (100 episodes); if it stays in this range, reported as "uncertain".
- **Freezing is a separate, auxiliary result.** The frozen first frame shows where the objects are, so it measures "no visual feedback after frame 1", not "no vision"; the image also drifts out of step with the robot state. It is not part of the reading rule and is reported on its own.
- **Statistics.** Success rates with Wilson 95% intervals.
- **Expectation.** LIBERO-Plus (arXiv:2510.13626) evaluated the same official checkpoint: ≤ 2% with every camera black (suite and episode count not stated, so only a weak reference). Expected: official π0 near 0 under both treatments.
- **What can and cannot be said.** Only whether this is a property of this checkpoint, not why: the two checkpoints differ in training data, steps, normalization and action representation. The 2026-10-28 correction above calls LeRobot's checkpoint "under-trained"; this experiment cannot test that, and the wording will be corrected with the results.
- **Not done now.** Official π0.5 (the conversion is still downloading; not scheduled yet); why LeRobot's π0 succeeds without vision; other suites.

## Official π0: the LeRobot conversion does not run, switching to OpenPI itself (2026-10-28, smoke stage, under "fix it if it fails" in the pre-registration above)

- **The conversion fails the smoke test.** `lerobot/pi0_libero_base` with the pre-registered fidelity steps (official mean/std, delta restoration, 5 executed steps, bfloat16), 50 normal episodes: **0/50**, with 96% of steps having actions outside [-1, 1]. The weights are loaded: 778/778 parameters equal the file one by one (the "Could not load state dict" message comes from 6 old-format normalization buffers in the file; PyTorch copies the parameters before raising).
- **Three controls (20 episodes each) are all 0/20:** a, the statistics embedded in the file and no delta (out-of-range steps drop to 3/5600, still 0); b, delta from the current step's state (what LeRobot v0.6.1 does); c, rendering at 256. Neither the statistics, the delta reference state nor the resolution is the root cause.
- **Two mismatches with OpenPI, checked in the source:** (1) the action statistics embedded in the converted repository look like raw actions without the state subtracted (dim 4 mean 0.001; the `norm_stats.json` that ships with this checkpoint in OpenPI's bucket has -2.97; the state statistics agree); (2) LeRobot v0.6.1's `lerobot_eval` post-processes every step separately and adds back the current step's state, while OpenPI adds the state at inference time to the whole chunk (`transforms.py` AbsoluteActions; `policy.py` passes the input state to the outputs). (2) is fixed on LeRobot main (`relative_action_processor.py` lines 148–152, PR #4057); this project applies the same semantics in `eval_probe.py`.
- **Primary sources.** A LeRobot maintainer wrote in [issue #2533](https://github.com/huggingface/lerobot/issues/2533) (2025-12-02) that the weights are the same as OpenPI's, but porting OpenPI's image processing and normalization into the LeRobot pipeline is not straightforward, so they fine-tuned instead of using this checkpoint as is; #2533, #4206 (also v0.6.1), #3638 and #2221 all report 0% for `*_libero_base` with `lerobot-eval`.
- **Switching to OpenPI itself (the fallback in the pre-registration).** OpenPI pinned at `215abfb2`, installed on the workstation from its `uv.lock`; checkpoint `gs://openpi-assets/checkpoints/pi0_libero` (19 files, 12.01 GB, each md5-checked), whose `norm_stats.json` has the same sha256 as the one used before. The OpenPI server (`scripts/openpi/serve_pi0_libero.py`) does the model, normalization, delta restoration and image resizing; LeRobot's LIBERO environment is the client (`POLICY_SERVER` in `eval_probe.py`), so environment, seed, initial states, blacking out and freezing are unchanged; "both slots masked" sets the slots' `image_mask` to 0 on the server.
- **Two deviations from the pre-registration.** (1) The smoke check "actions within [-1, 1]" was my own and was not checked against OpenPI's actual output range; the conversion fails it, but it cannot decide correctness alone. (2) OpenPI renders at 256 as its script does; the earlier runs used 360, so first-frame hashes cannot be compared with them episode by episode. Initial states are set by episode index (LeRobot `envs/libero.py` lines 168–175, 345–346, independent of resolution); each episode's first end-effector position is compared with the earlier runs' trajectories instead.
- **Stop rule (set at 16:45, before the smoke result).** If OpenPI's own implementation also fails the smoke test, no further debugging: the process is recorded as is, the README keeps "very likely" with the LIBERO-Plus citation, and no ablation results are reported. If it passes, the gate and the ablations run as pre-registered.

## Official π0: gate and ablation results (finished 2026-10-28, read by the pre-registration above)

- **Smoke test and gate (OpenPI itself).** Smoke 50/50. Normal, 500 episodes: **482/500 = 96.4%** (Wilson 94.4–97.7%), passing the 92% gate and matching the 96.8% in the earlier OpenPI README; per task 49, 50, 48, 50, 49, 44, 50, 49, 45, 48; actions out of range on 14/56008 steps.
- **Initial states.** The first-step end-effector position matches LeRobot π0's 500-episode normal run (`dashboard/data/s500/pi0_none`) on 500/500 episodes, maximum difference 0 (the 100-episode runs against the first 10 per task, also all 0). The new LeRobot slot-masked run renders at 360 and its first-frame hashes match that run on 100/100. Recomputed in `results/official_pi0_summary.csv` by `scripts/analysis/make_figures.py`.
- **Ablations (100 episodes each).**

| Treatment | Official π0 (OpenPI, 256 rendering) | LeRobot π0 v044 (LeRobot, 360 rendering) |
|---|---|---|
| All black | **0/100** (0–3.7%) | 273/500 (five runs of 100, 53–56%) |
| Both slots masked | **0/100** (0–3.7%); the server reports all three masks False | **35/100** (26.4–44.7%); per task 0, 8, 7, 2, 0, 5, 7, 0, 6, 0 |
| Both frozen (auxiliary) | 0/100 | 71/100, 80/100 |

- **Baseline for the 100-episode runs.** The 100-episode runs use the first 10 initial states of each task; on those 100 states official π0 scores 93/100 normally and LeRobot π0 65/100 (both taken from their 500-episode runs). LeRobot π0's five all-black runs are these same 100 states run once each, so 273/500 is not 500 independent episodes.
- **Reading.** Official π0 is ≤ 10% under both treatments; LeRobot π0 is ≥ 40% all black but 35% < 40% slot-masked. By the rule: succeeding without vision is a property of this checkpoint, not of π0 in general; **this rests on the all-black comparison only**.
- **A difference not foreseen, stated here.** After switching to OpenPI itself, the two sides differ not only in weights but also in inference pipeline (JAX vs PyTorch, image resizing, the normalization and delta-restoration code, noise source) and rendering resolution (256 vs 360). The same official weights score 0/50 in the LeRobot pipeline and 50/50 in OpenPI's, so the pipeline alone can make the difference between 0% and 96%. "A property of this checkpoint" therefore means "this checkpoint together with its inference pipeline"; it cannot be attributed to the weights alone. Supporting evidence: in the same LeRobot pipeline and environment, π0.5 v044 scores 0% all black, so the LeRobot pipeline by itself does not make a policy succeed without vision; π0.5 and π0 are different models, though, so this does not replace a control. On the official side the diffusion noise comes from the server process's random state and is not bit-for-bit reproducible.
- **Two ways of removing vision differ on the same checkpoint.** LeRobot π0 slot-masked, 35/100, is below all black (53–56/100): paired by initial state against each of the five all-black runs, McNemar p ranges from 0.0015 to 0.0064, significant every time. What remains depends on how vision is removed.
- **Correction.** The 2026-10-28 correction above calls LeRobot's checkpoint "under-trained", and the 2026-10-06 "the public checkpoint is under-trained" paraphrases the #2114 maintainer, who was speaking of an earlier checkpoint. This project never tested training: LeRobot π0 v044 scores 72–73% normally and official π0 in OpenPI's pipeline 96.4%; the cause of the gap is unknown, and the pipeline alone can produce large differences. "Under-trained" in the README, the dashboard and the paper is replaced by a statement of fact.
- **Raw data.** `dashboard/data/official_pi0/`: `ojx_*` are the OpenPI runs, `pi0_drop_all` the LeRobot π0 slot-masked run, `opi0_*` the conversion's smoke test and three diagnostics (0/50, 0/20 × 3, kept as a record); each directory has `eval_info.json`, `first_frame_hash.json` and `first_eef.json` (first-step end-effector position per episode).

## Official π0 with one camera: pre-registration (2026-10-29 08:00, before running; local only, not pushed)

- **Question.** How much does official π0 (OpenPI itself) keep when only one camera is removed: wrist masked only, or main view masked only? Removing both gives 0/300; this tells which camera it cannot do without, and checks whether the 0% merely reflects a pipeline that breaks under any perturbation.
- **Design.** Identical to the ablation above: OpenPI server, 256 rendering, 5 executed steps per chunk, same initial states; `BLACKOUT=drop_wrist` / `drop_agent`, the server sets that slot's `image_mask` to 0 and the client asserts the reported mask is False; 100 episodes each (10 per task). No blackout variants, no other arms.
- **Reading (against the official normal 96.4%).** Success ≥ 85% → that camera can be removed; ≤ 50% → it depends on that camera; in between → partial dependence, no conclusion. Each camera is read separately.
- **Expectation (written down so it cannot be revised afterwards).** Masking the wrist drops clearly (< 85%); masking the main view drops less. Low confidence.
- **Comparisons and limits.** LeRobot π0 v044 gives 71.2% / 72.6% (wrist masked) and 74.2% (main view masked); π0.5 v044 gives 4.6% / 55.4% (500 episodes each, 360 rendering, LeRobot pipeline). Shown side by side only, not part of the reading; the pipelines differ, so differences cannot be attributed to the weights.

## Official π0 with one camera: results (2026-10-29, read by the pre-registration above)

- **Results (100 episodes each; the server reports the masked slot as False).** Wrist masked only: **0/100** (Wilson 0–3.7%, all 10 tasks 0). Main view masked only: **77/100** (67.8–84.2%; per task 8, 9, 10, 8, 5, 3, 9, 6, 9, 10), below the normal 93/100 on the same 100 initial states (paired: 21 succeed normally and fail masked, 5 the other way; McNemar p = 0.0025).
- **Reading.** Wrist: ≤ 50% → depends on the wrist camera. Main view: between 50% and 85% → partial dependence, no conclusion (even the upper bound, 84.2%, is below 85%). Both expectations held. The 85% / 50% thresholds were set after seeing 0/300 with both cameras removed and before the single-camera runs; readers should weigh that.
- **Scope.** This removes one camera at test time; it is not training with one camera, which this project has not done (in the literature, OpenVLA-OFT trained on the third-person camera alone reaches 96.2% on Spatial).
- **Side by side with LeRobot (not part of the reading; different pipelines).** Official π0's pattern (zero without the wrist, a partial drop without the main view) runs the same way as π0.5 v044 (4.6% / 55.4%); LeRobot π0 v044 barely drops without either camera (71.2% / 74.2%, normal 72.0%). The pipelines differ, so the exact numbers are not compared.
- **0 deviations**; the pre-registration is local only, without a public timestamp.

## Official π0 at 360 rendering: pre-registration (2026-10-29 15:05, before running; local only, not pushed)

- **Question.** Official π0 renders at 256 and LeRobot π0 at 360; both are resized to 224 before the model. Is resolution a confounder between the official 0% and LeRobot's 53–56%?
- **Design.** Official π0 with the same OpenPI server, rendering switched back to 360 (as on the LeRobot side); normal, all black and both slots masked, 100 episodes each (the first 10 initial states per task). First-frame hashes are compared episode by episode with `s500/pi0_none` (both 360, so all should match).
- **Reading.** Normal: paired against 93/100 at 256 on the same 100 states; McNemar p ≥ 0.05 and success ≥ 85% → resolution does not affect normal performance. All black and slot-masked both ≤ 10% → the official 0% does not depend on resolution and the earlier conclusion stands; either > 10% → resolution is a confounder, reported as such, and the earlier reading is withdrawn.
- **Expectation.** All three match the 256 runs (normal about 90%, the other two 0%).

## Official π0 at 360 rendering: results (2026-10-29, read by the pre-registration above)

- **Results (100 episodes each).** Normal **99/100** (Wilson 94.6–99.8%); all black **0/100**; both slots masked **0/100** (the server reports all three masks False). First-frame hashes of all three runs match the same 100 initial states of `s500/pi0_none` episode by episode (100/100).
- **Reading.** Normal, paired against 93/100 at 256: 1 succeeds at 256 and fails at 360, 7 the other way, McNemar p = 0.070 ≥ 0.05, and 99% ≥ 85% → resolution does not affect normal performance. All black and slot-masked are both 0% ≤ 10% → the official 0% does not depend on resolution, and the earlier conclusion stands. The expectation held; 0 deviations.
- **What it means.** Rendering resolution now matches on both sides, so that confounder is removed; what remains is the weights plus the inference pipeline. First-frame hashes can now be compared with the LeRobot side directly, without the end-effector substitute.
- Raw data in `dashboard/data/official_pi0/ojx360_*`.

## Correction (2026-10-29): tightening the reporting after an external review

- **An advance record is not a pre-registration.** Only the official π0 pre-registration was pushed before its results (commit `6c54c5d`). The "pre-registrations" for the section 1.4 single-camera experiment, the official π0 single-camera runs and the 360 rendering runs, and the stop rule, were written down only locally, without a public timestamp, so they are advance records; the 85% / 50% thresholds for the official single-camera runs were also set after seeing 0/300 with both cameras removed. Their results count as exploratory. The README is updated.
- **LeRobot π0's normal baseline is not one number.** The 65/100 used in "gate and ablation results" above comes from the first 10 episodes per task of `s500/pi0_none`, the lowest of 7 normal runs on the same 100 initial states (76, 65, 74, 73, 72, 76, 71; mean 72.4). Pairing the first all-black run (56/100) with each of the 7 gives McNemar p = 0.19 against the 65 run and 0.001–0.036 against the other six. Whether all black is significantly below normal therefore depends on which normal run is chosen; from now on the range over the 7 runs is reported instead of a single run.
- **The five all-black runs are not 500 independent episodes.** They are the same 100 initial states run once each. The 273/500 in the summary is the sum of the five runs and must not be tested as 500 independent episodes; against slot masking only the range of the per-run paired comparisons is reported (McNemar p 0.0015–0.0064), not one pooled test.
- **Success is largely set by the initial state.** Over section 1.4's 7 π0 runs of 500 episodes, 120 of the 500 initial states succeed every time and 9 fail every time. How much the scene varies within a task has not been measured; the next step, an open-loop replay baseline, addresses that.

## Official π0 with only the wrist camera frozen: advance record (2026-10-29 17:41, before running; local only, not pushed)

- **Question.** Official π0 with only the wrist camera masked scores 0/100. Masking is an input form a real camera slot never had in training; is the 0% due to the missing wrist image or to the unfamiliar input form?
- **Design.** Identical to `ojx_drop_wrist` (OpenPI server, 256 rendering, the same 100 initial states, 5 executed steps per chunk), except that the wrist camera gets the episode's real first frame for the whole episode with its mask kept True; the main view updates as usual. `BLACKOUT=freeze_wrist`, results in `ojx_freeze_wrist`.
- **Smoke evidence (printed every run).** The server reports the wrist slot mask as True; at step 20 of episode 1 the wrist image differs from frame 1 by 0 and the main view by more than 0; each episode sends exactly 1 distinct wrist image and more than 1 main-view image.
- **Reading (as in the single-camera advance record).** ≥ 85% → the wrist camera can be removed; ≤ 50% → it needs a wrist image that updates over time (as π0.5 does), and the 0% under masking is not caused by the input form; 50–85% → no conclusion. McNemar against `ojx_drop_wrist`, paired by initial state, is also reported: if clearly above 0/100, part of the masking 0% comes from the input form.
- **Expectation.** ≤ 50%.

## Open-loop replay baseline: advance record (2026-10-29 18:20, before running)

- **Question.** LeRobot's π0 still scores 53–56% with all cameras black. How much do the initial states of one LIBERO-Spatial task differ? Without looking, how often does repeating one fixed action sequence per task succeed? If fixed sequences reach a similar rate, "succeeding without vision" says more about the benchmark than about the policy.
- **Design.** Official π0, OpenPI server, 360 rendering, normal condition, on the same 100 initial states (the first 10 per task), logging every action actually passed to `env.step` (the `act` field of `eval_probe.py`); results in `ojx360_replay`. Then, with no model, in LeRobot's `LiberoEnv` (same seeds as the evaluation, 10 no-op steps at the start, relative control):
  - self-replay (control): each successful episode's actions replayed on its own initial state;
  - cross-replay: replayed on the other 9 initial states of the same task;
  - scene variation: the position of every object in all 50 official initial states of each task.
  Entry point `run_official_pi0.sh replay`, replay script `scripts/analysis/replay_open_loop.py`.
- **Validity condition.** Self-replay success ≥ 80%; otherwise replay itself is unreliable, the baseline is void, and only scene variation is reported. The pilot (LeRobot π0, 2 episodes per task) gave 12/13: replaying the same actions drifts by millimetres during contact, even with the evaluation's reset seeds. So self-replay success is the noise floor, and cross-replay results are read against it.
- **Measure.** For each task, take the action sequence with the most cross-replay successes and compute its success rate on the other 9 states, then average over the 10 tasks ("the best fixed sequence per task"). The pooled success rate of all cross-replays is also reported.
- **Reading.** Against LeRobot π0's 53–56% all black: best fixed sequence ≥ 40% on average → the benchmark lets fixed sequences reach most of the success without vision, and LeRobot's result mainly reflects the benchmark; ≤ 10% → fixed sequences are not enough, and LeRobot's π0 without vision still uses the robot state to act differently per state; 10–40% → partial, no conclusion.
- **Expectation.** 10–40%: objects are only slightly perturbed within a task, so some cross-replays succeed, but fewer than with all cameras black. Not confident.
- **Limits.** The actions come from official π0 with vision; replay only tests whether that trajectory still works in other states, and is not the best blind policy. The best of 10 sequences is selected after the fact, so it is optimistic.

## Official π0 with only the wrist camera frozen: results (2026-10-29, read by the 17:41 advance record, which was pushed before the results in commit `c7e9023`)

- **Result (100 episodes).** **0/100** (Wilson 0–3.7%, 0 in all 10 tasks). The smoke evidence is complete: the server reports both the wrist and main-view masks as True; at step 20 the wrist image differs from frame 1 by 0 and the main view by 0.62; each episode sends 1 distinct wrist image and 56 main-view images. First-frame hashes and end-effector positions match `ojx_drop_wrist` episode by episode (100/100).
- **Reading.** ≤ 50% → official π0 needs a wrist image that updates over time, and the 0% under masking is not caused by the input form. Paired against `ojx_drop_wrist`: both 0/100, 0 discordant pairs, McNemar p = 1. As expected; 0 deviations.
- **Side by side (not part of the reading; different pipelines).** LeRobot π0 v044 with only the wrist frozen scores 72.8% (500 episodes); π0.5 v044 scores 0.0%.
- Raw data are in `dashboard/data/official_pi0/ojx_freeze_wrist`.
