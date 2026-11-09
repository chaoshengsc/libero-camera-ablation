# Study structure and experiment coverage

[中文](STUDY_MAP_CN.md) · [Overview](../README.md) · [Full experiments](EXPERIMENTS.md)

**Four-policy exploration, two-policy wrist-treatment follow-up; official π0 and P1/P2 provide separate interpretation controls.** The four policies did not receive the same full intervention suite. This is not a complete factorial design. “Untested” is distinct from failure or 0% success.

## 1. Policy coverage narrows across experimental stages

| Public checkpoint | Visual inputs | Early exploration | Later wrist-treatment study | Supplementary agent-view condition |
|---|---|---|---|---|
| LeRobot π0 v044 | Agent + wrist | Single/all black, both-camera noise, both frames frozen | Normal/wrist black/wrist mask/wrist frozen; 500 episodes, selected repeats | Agent mask, 500 episodes |
| LeRobot π0.5 v044 | Agent + wrist | Single/all black, both-camera noise, both frames frozen | Normal/wrist mask/wrist frozen, 500 each; wrist black borrows five earlier 100-state repeats | Agent mask, 500 episodes |
| SmolVLA `31d453f7` | Agent + wrist | Single/all black, both-camera noise, both frames frozen | Mask and wrist-only freezing **untested** | Agent mask untested |
| OpenVLA | **Agent only** | Agent black (its entire visual input) | Wrist conditions inapplicable | No additional mask/freeze/noise tests |

The four-policy blackout overview and two-policy wrist figure describe different scopes. Official π0/OpenPI is an additional checkpoint/pipeline control, not a fifth model family or the same checkpoint as LeRobot v044.

## 2. Main experiment: change the wrist treatment, keep the agent view live

The pre-run design specifies one variable with four levels: normal, black image, original-slot masking and frozen first wrist frame. The checkpoint, instruction and processing rules stay fixed; the agent view and proprioceptive state update live with the environment. Matching initial states does not imply identical later trajectories or policy noise. π0 and π0.5 retain their own inference protocols, so the columns are not a common-protocol model ranking.

| Wrist treatment | π0.5 v044 | π0 v044 | Evidence structure |
|---|---|---|---|
| Normal | 492/500 = 98.4% | 360/500 = 72.0% | Current normal baselines; 10 tasks × 50 states |
| Black image, mask true | 0/100, repeated five times | 352/500 = 70.4% | π0.5 borrows historical repeats of 100 states, not a paired 500-state arm |
| Original-slot mask false | 23/500 = 4.6% | 356/500 = 71.2% | Paired with each checkpoint's 500-state baseline; π0 repeat 363/500 |
| First wrist frame frozen | 0/500 = 0.0% | 364/500 = 72.8% | **Wrist only; agent view continues updating** |

**Separate supplementary condition:** agent view masked, wrist live: π0.5 277/500 = 55.4%, π0 371/500 = 74.2%. This is not a complete four-level agent-view experiment: agent-only freezing and single-camera noise were not run.

[Episode-level pairing](../results/single_camera.csv) · [Main results](../results/single_camera_summary.csv) · [Intervention implementation](../scripts/eval/eval_probe.py)

## 3. Show the missing conditions

Actual π0.5 coverage, preserving intervention types and denominators:

| Intervention | Wrist only | Agent only | Both cameras |
|---|---|---|---|
| Black image | 0/100, five repeats | 51/100, 57/100 | 0/100, two repeats |
| Original-slot mask | 23/500 | 277/500 | **Untested** |
| First-frame freezing | 0/500 | **Untested** | 0/100, two repeats |
| Gaussian noise | **Untested** | **Untested** | 99/100, 97/100 |

Blackout and masking are different operations. Freezing changes both image updates and image–state synchronization. A supported script mode does not establish a completed run. Early 100-state baselines use the first ten initial states per task; later 500-state conditions use fifty per task. Repeats do not create more independent initial states.

## 4. Separate questions for the additional controls

| Control | Question | Matching and limits |
|---|---|---|
| Official π0/OpenPI | Check all-black behavior in another π0 checkpoint and pipeline | Matched 100 normal: 93/100 official, 65/100 LeRobot. Full 500 normal 482/500 and 360/500 are separate references. Weights and pipelines both change |
| π0 P1: live/frozen state × normal/black images | Measure state-update sensitivity in LeRobot π0 v044 | Its own three-repeat paired baselines; not the wrist-study normal condition, and not unique evidence of online correction |
| P2 fixed-action replay | Measure the success of preselected actions on selection-excluded states | Official π0 source; 262/400 targets; no policy calls. Cannot be subtracted from P1 to assign mechanism contributions |
| Checkpoint identity, CPU loading, 220-step recount | Verify the identity and protocol evidence for existing results | Engineering/provenance checks, not new behavioral interventions |

Every point in the official-control figure uses the first ten states per task, 100 episodes per point. Repeats appear individually; no pooled Wilson interval treats five executions of the same 100 states as 500 independent states. Full 500 results remain in the original summary. The new [matched 100 table](../results/official_pi0_matched100.csv) records the subset explicitly.

## 5. Presentation issues corrected in this revision

- The four-policy introduction did not explain why detailed figures covered only two policies.
- Wrist main conditions and the supplementary agent-mask condition appeared as equal experiment arms.
- Both-camera noise/freezing labels omitted their target, obscuring wrist-only versus both-camera freezing.
- The broad “500 per condition” label hid π0.5's borrowed five-repeat wrist-black evidence.
- A 500-state normal rate appeared next to 100-state interventions without the matched 100 baseline.
- Pooled Wilson intervals conflated repeated executions with independent states.

This audits consistency between public sources, pre-run records, intervention code and presentation. It does not revalidate every private image/tensor, and no missing condition was rerun. Historical logs and frozen tags remain unchanged. The separate fine-tuning project is outside scope.

“Matched 100” means the same task/init indices; it does not establish bitwise-matched policy noise or complete simulator states.

## Follow-up work will complete the remaining applicable controls

Agent-only masking already has 500-episode results; agent-only blackout has earlier 100-episode repeats. The wrist main study and supplementary agent mask are complete. The following unstarted follow-ups extend controls and policy coverage; they are not current results.

### The main study will add these controls

| Incomplete condition | Current boundary | Planned follow-up |
|---|---|---|
| Full agent-view single-factor study for π0/π0.5 | Only masking entered the later 500-state study; agent-only freezing is absent and black uses earlier 100-state runs | Add agent-only freezing and blackout matched to the main-study scale, keeping the wrist live |
| π0.5 both-camera masking | Normal, wrist mask and agent mask exist; both-mask is absent | Add both-mask to complete the four camera-availability conditions |

### Further work will extend policy and intervention coverage

| Incomplete condition | Current boundary | Planned follow-up |
|---|---|---|
| Single-camera noise | Existing noise affects both cameras together | Add separate agent-only and wrist-only noise for applicable dual-view policies |
| SmolVLA masking and wrist-only freezing | Current evidence is early blackout and both-camera noise/freezing | Verify interface and slot semantics, then add applicable single-camera masks and wrist-only freezing |
| Other OpenVLA single-view interventions | Only blackout of its sole agent view is tested; freezing/noise are absent | Add first-frame freezing and noise for the sole view, and verify mask-interface applicability |

OpenVLA has no wrist input; wrist conditions are inapplicable rather than missing or pending results. Each follow-up will first fix its checkpoint, matched normal group, tasks/states, intervention and episode count. Results will be added after execution and acceptance. These plans do not establish a started run.
