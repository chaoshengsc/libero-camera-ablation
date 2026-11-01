# Existing-run protocol evidence

[中文](#中文说明) · [Experiments](../../../docs/EXPERIMENTS.md#3-evaluation-protocols-and-audit-scope)

This directory contains retrospective CPU audits plus an explicitly authorized
CPU policy-loading check. No policy forward or simulator was run.
Original success labels, checkpoint files and published 280-step results are unchanged.

| File | Scope |
|---|---|
| [provenance.json](provenance.json) | 79 core records plus 16 P1 runs: original-file hashes and association methods.75 canonical JSON matches, one ACT JSON match, three ordered OpenVLA text logs, and 16 hash-bound P1 records. |
| [episode_lengths.json](episode_lengths.json) | 13150 recorded episode lengths across 90 runs. Columns identify task/state, control steps and available action/EEF/video witnesses. Missing witnesses are null, not fabricated. |
| [checkpoint_identity.json](checkpoint_identity.json) | Rechecked 19-file native manifest and fixed-revision HF LFS hash; pinned CPU array mapping finds 775 comparable tensors different under declared precision. |
| [checkpoint_loading.json](checkpoint_loading.json) | One authorized CPU model load: all 778 model-state entries match the HF candidate after target-dtype conversion despite the six legacy-buffer warnings. No inference or rollout. |

Video slicing in the recorded LIBERO batch1 evaluator retains exactly one frame
per control step, not steps+1. Cross-checks cover 6110 older EEF/video pairs,
100 older action/video pairs and all 1240 P1 action/video pairs, with zero length
mismatches. Source hashes and the recorded audit support the export; complete
videos/NPZs remain outside Git. This export does not make those artifacts public.

Only the first ten videos per task survive for three early 500-episode normal
baselines. Their deadline rows are explicitly `matched100`, with source_episodes=500
and episodes=100. OpenVLA already used 220 steps; its outcomes need no inferred
duration. ACT/PushT have other environments and are excluded from this deadline
comparison. The four failed HF-candidate diagnostics remain diagnostics, not
validated native-checkpoint controls. Repeats are reported separately, not pooled
as independent states. This recount is not a new upstream-protocol evaluation.

From the repository root, run:

```bash
python scripts/analysis/summarize_protocol_audit.py
```

It checks required source-association metadata, public-result/duration hashes,
episode coverage, length agreement and the managed
[budget CSV](../../../results/budget_sensitivity.csv), using only the standard
library. Mismatch/missing evidence exits nonzero. `--write` regenerates only that
repository-managed CSV after source review; it does not run a model. CI cannot
rehash raw artifacts outside Git; their recorded hashes remain audit references.

For an independent raw checkpoint check, use the configured Linux OpenPI
environment in the [setup guide](../../../docs/OPENPI.md). At the repository root,
with `OP_CKPT`, `OP_SRC`, `OP_ENV` and `EMB_ROOT` set as there:

```bash
NATIVE_PARAMS="$OP_CKPT/params"
HF_CHECKPOINT="$EMB_ROOT/ckpt/pi0_libero_base@98ac51b8/model.safetensors"
CONVERTER="$OP_SRC/examples/convert_jax_model_to_pytorch.py"
AUDIT_JSON="$EMB_ROOT/logs/checkpoint_identity_01.json"
"$OP_ENV/bin/python" scripts/analysis/check_checkpoint_identity.py \
  "$NATIVE_PARAMS" "$HF_CHECKPOINT" "$CONVERTER" --output "$AUDIT_JSON"
```

The assignments select existing native parameters, the fixed HF candidate,
the pinned official mapping and an unused JSON output. The script checks the
mapping SHA before executing only its two array functions, substituting NumPy
containers for Torch wrappers without changing arithmetic. It never imports
Torch/JAX/models or writes weights; it needs TensorStore and more than 40 GiB free
RAM, with native float32 arrays bounded below 16 GiB. An existing output is rejected.
The observed result exits 1 with `DIFFERENT_UNDER_REFERENCE_MAPPING`; this is a
negative identity result, not a successful conversion or a failed simulation.
Incomplete matches/invalid inputs exit 2, and only complete mapped matching exits 0.
Even exit 0 does not prove functional equivalence or a unique failure mechanism.

The separate A0 loading check reads the loaded `state_dict()` against the HF file,
not against native GCS parameters. Its 778 entries use 777 source keys because of
the declared tied embedding alias; they are not 778 independent tensors.
All match after target-dtype casting (523 float32, 255 bfloat16), with no missing,
unknown, differing or nonfinite model entries. The caught strict-load warning for
six obsolete normalization buffers remains. The CPU result does not recreate the
historical GPU state or test actions, processors or simulator behavior. Source
fingerprints, per-entry counts, loader output, script/raw-report hashes and the
74.593-second execution receipt are retained in the metadata. The exact A0
instrumentation remains a local audit artifact; this export does not supply it
or make the full runtime replayable. This result does not reverse the failed
native/HF identity check or establish a unique reason for the old 0/50 score.

P1's full policy-image tensors and stepwise terminal flags were not saved and
remain absent. Environment-view videos are not the two camera tensors received
by the policy. The recovered lengths and assertions strengthen execution
acceptance; they cannot restore missing fields or identify online correction.

## 中文说明

本目录含既有工件的CPU回溯审计和另行授权的CPU策略载入核验，没有策略前向或新仿真，
也没有改写原成功标记。
95组来源包括79组核心记录和16组P1；六次旧补跑已用完整JSON关联，OpenVLA用有序
逐回合文本关联，不能只用相同的全零成功数识别运行。

13150条控制步记录保留实际可用的动作/末端/录像长度，缺失证据写null。三组早期
500回合正常评测只重计每任务前10回合，标为matched100，不外推缺少录像的400回合。
OpenVLA原本就是220步；ACT/PushT不参与本次截止比较。重复不合并成独立状态。
首条命令只读核查来源关联字段、公开结果/长度哈希、覆盖和CSV，失败返回非零；
CI不能重新核验Git外工件内容，其原始哈希是审计指针。`--write`仅重建仓库管理的补充CSV。

原始权重核验需按OpenPI指南先配置上述四个变量，再设置已有输入路径与未用JSON路径。
最后一条命令需要已有NumPy/TensorStore和超过40GiB空闲内存，全程CPU，不导入模型、
Torch/JAX，不写权重。已存在输出、来源源码指纹不同或输入无效会被拒绝；返回1表示
观察到参数不一致，返回2表示证据不完整/错误，返回0也只核对映射参数，不证明功能等价。
原生19文件MD5和HF固定revision的LFS SHA均通过；775个可比较张量在声明精度下均不同，
所以不能把旧HF检查点0/50当成同一官方权重仅换管线的结果，也不据此宣称唯一失败原因。

另行授权的A0核验比较的是载入后的`state_dict()`与HF文件，不是原生GCS权重。
778条状态字典项使用777个不同源键（含共享embedding别名），不能当成778个独立张量；
按目标dtype比较全部一致（523个float32、255个bfloat16），缺失/未知/不一致/非有限项为0，
6个旧归一化buffer的严格加载告警仍保留。本次74.593秒CPU重检不还原历史GPU状态，
也未测试动作、处理器或仿真行为。元数据保留输入指纹、逐条计数、加载输出及脚本/原报告哈希；
具体A0取证脚本仍属本地工件，公开导出不提供它或使完整运行可重放。同源性失败结论不变，
不能由此确定旧0/50的唯一原因。

完整录像/NPZ仍在Git外；公开元数据不替代它们。P1原完整模型图像与逐步终止字段
仍缺失，环境录像也不等于模型收到的两路图像。补证加强了执行验收，不能补造字段或识别唯一机制。
