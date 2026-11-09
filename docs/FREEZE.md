# Camera ablations · evidence freeze

**v1.5.2 · 2026-11-09**

[中文](FREEZE_CN.md) · [Project overview](../README.md) · [Full experiments](EXPERIMENTS.md) · [Interactive results](https://chaoshengsc.github.io/libero-camera-ablation/dashboard/?lang=en)

This version fixes the public camera-ablation results, analysis code, protocol audits and interpretation limits. **It archives existing evidence; no training, inference or simulation was added.** The independent fine-tuning project is outside this freeze and update. The freeze date is an archival date, not the date of every experiment.

This revision clarifies scope and repeated-state reporting: [study structure](STUDY_MAP.md) separates four-policy exploration, three-policy perturbations and the two-policy wrist study. The v1.5.1 tag is unchanged.

## Findings and their evidence

| Question | Observed result | Verify |
|---|---|---|
| Can tasks succeed without images? | Tested π0.5, OpenVLA and SmolVLA score 0% with all-black images; LeRobot π0 v044 scores 53–56% over five 100-episode runs | [Per-task counts](../results/blackout_per_task.csv) · [Raw evaluations](../dashboard/data/) |
| Does official π0 do the same? | Matched100: official π0/OpenPI normal93/100, black0/100; LeRobot π0 v044 normal65/100, black53–56/100 across five runs | [Official comparison](../results/official_pi0_summary.csv) · [Raw records](../dashboard/data/official_pi0/) |
| How sensitive is π0.5 to its wrist view? | Normal 492/500; wrist masked in its original slot 23/500; wrist frozen at the first frame 0/500 | [Paired statistics](../results/single_camera_summary.csv) · [500-episode records](../dashboard/data/s500/) |
| Do state updates matter for π0 v044? | P1 three-run means: normal/black 73.3%/55.3%; freezing the first model state gives 0% in both | [Run-level results](../results/state_feedback_runs.csv) · [Paired differences and intervals](../results/state_feedback_comparisons.csv) |
| Can fixed actions also succeed? | P2 selection-excluded replay: 262/400 = 65.5%, stratified-bootstrap 95% interval 61.0–69.75%; self-replay 10/10 | [Aggregate and per-task results](../results/replay_holdout_summary.csv) · [Selection and outcomes](../dashboard/data/replay_holdout/) |

Black images, slot masking, key deletion and freezing are distinct interventions. This table combines observations across experiments, not a model ranking under one shared protocol. [Five-checkpoint reference comparisons](../results/reproduction.csv) remain available; ACT/PushT are outside the four-policy LIBERO camera study.

## What this freeze consolidates

Starting from the public P1/P2 results in v1.5, this snapshot includes the subsequent engineering and protocol evidence already in the repository, with a single reading path:

| Archived material | What can be checked | What remains outside its scope |
|---|---|---|
| [95 source associations and 13,150 duration rows](../dashboard/data/protocol_audit/) | Public results, available trajectory/video lengths and recorded hashes | Full videos, NPZs and private source artifacts are not thereby public |
| [Common 220-step recount](../results/budget_sensitivity.csv) | Deadline sensitivity within available evidence; explicit matched100 coverage | A full new common-protocol evaluation or inferred missing episodes |
| [Checkpoint identity](../dashboard/data/protocol_audit/checkpoint_identity.json) and [loading audit](../dashboard/data/protocol_audit/checkpoint_loading.json) | Identity not established; 778/778 loaded HF state entries match source tensors at target precision (777 source keys, including a tied alias) | A same-weight pipeline control, policy inference or behavioral equivalence |
| Execution entries and offline checks | Current failure propagation, artifact protection, setup checks and CI | New-machine or real-robot qualification |
| [Evidence SHA-256 manifest](../results/freeze_20261109_v1.5.2.sha256) | Whether listed public raw records and result files changed | Verification of private payloads, unavailable weights or research claims |

## Interpretation limits and deferred work

- **Checkpoint and pipeline stay coupled.** Official π0/OpenPI and LeRobot π0 v044 change both weights and inference paths. Their difference cannot uniquely identify conversion, training adequacy or one implementation detail. The HF candidate failed the identity check and is not a same-weight control.
- **Keep the repeated-state structure.** Five π0 blackout runs reuse the same 100 initial states. P1 repeats preserve state pairing. P2's 400 target states were excluded from action selection but appeared in earlier evaluations; they are not a hidden test set.
- **The mechanism remains unidentified.** P1 supports state-update sensitivity; P2 supports the viability of the selected fixed actions. Subtracting their rates cannot estimate a mechanism's contribution. Frame freezing changes both visual updates and image–state synchronization; the low-level controller still uses feedback.
- **Deferred work stays deferred.** P3 delay and the proposed disturbance-recovery study remain deferred/unrun. This freeze does not resume them or include the separate fine-tuning project or new success rates.
- **Public evidence has limits.** Papers, PDFs, weights, tokenizers, full NPZs, private materials and internal troubleshooting records are excluded. Historical notes retain their original claims and corrections; current interpretation is given here, in the [experiments](EXPERIMENTS.md) and in the public source records.

## Verify and cite

From the repository root, using an existing analysis environment; none of these commands runs a policy or simulator:

```bash
python scripts/checks/freeze_check.py
python scripts/analysis/summarize_protocol_audit.py
python scripts/checks/repository_check.py
```

The first checks the SHA-256 of every listed public evidence file; the second validates the protocol export and derived table; the third checks public links, JavaScript syntax and version consistency. See the [results directory](../results/README.md) for CSV/SVG regeneration. The **Git commit referenced by v1.5.2** fixes all code, documentation and environment configuration; the evidence manifest covers only its listed public data and result files.

Cite `v1.5.2`, the actual commit SHA and the data paths used. Earlier tags remain unchanged. Future corrections should use a new commit/version with an explicit explanation, without moving this frozen tag.
