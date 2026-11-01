# State-input update sensitivity (P1)

[中文](#中文说明) · [Experiment report](../../../docs/EXPERIMENTS.md#17-state-input-update-sensitivity)

Sixteen runs are included: four ten-episode engineering checks and three paired
repeats of four conditions, each with 100 episodes. Only the 1,200 formal episodes
enter the comparisons; they represent 100 distinct task/initial-state pairs.

- `metadata.json`: checkpoint, effective protocol, original source hashes and
  hashes of the published records.
- `<stage>_<group>/eval_info.json`: original evaluation outcomes; local video
  path prefixes are replaced with `${EMB_ROOT}`.
- `<stage>_<group>/pairing.json`: exported episode identities, image hashes,
  policy-noise seeds and input-check counters from the original evidence JSON.
- `audit.json`: the completed full-artifact audit and its limitations.

Run `python scripts/analysis/summarize_followup.py` from the repository root,
using Python with NumPy. It verifies coverage/pairing and recomputes the
within-task bootstrap with all repeats and conditions kept together.

Full per-block state/action NPZ files remain outside Git. The public records
reproduce outcome statistics, not the full tensor-level audit. Termination
flags and full image tensors were not saved in P1; the audit does not invent
them. A frozen model input is not fixed-action replay or a feedback-free system.

## 中文说明

本目录包含40回合工程检查与1200回合正式评测；只有正式回合进入主统计，
三轮重复对应100个不同初始状态。元数据保留权重、协议、来源及公开文件哈希；
逐运行 JSON 保留成功标记和配对元数据，可独立重算统计。

完整逐块状态/动作 NPZ 留在 Git 外；`audit.json`记录其已有验收，
不表示公开文件可以重做全部张量验收。P1 未记录的逐步终止标记、完整图像仍属缺口。
冻结模型状态不等于固定动作回放，也不等于整个系统没有反馈。
