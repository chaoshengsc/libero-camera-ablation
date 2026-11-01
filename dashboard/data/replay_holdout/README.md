# Fixed-action replay on selection-external states (P2)

[中文](#中文说明) · [Experiment report](../../../docs/EXPERIMENTS.md#16-fixed-action-replay)

- `selection.json`: the frozen ten per-task choices, target states, original
  source-file hashes and action-array hashes. Choices were fixed before P2.
- `source_actions.json`: the ten selected float32 action arrays, losslessly
  exported from the original NPZ and checked against the frozen array hashes.
- `outcomes.json`: all ten self-replays and all 400 formal outcomes. The export
  retains original episode identities, stopping reasons and evidence hashes.
- `metadata.json`: export/source provenance and file hashes.
- `audit.json`: the completed audit of all 410 original NPZ episode records.

From the repository root, `python scripts/analysis/summarize_followup.py`
recomputes the per-task Wilson intervals and the fixed-task stratified bootstrap.
It requires NumPy, no GPU, policy or simulator.

To repeat the simulation, see [replay_holdout.py](../../../scripts/analysis/replay_holdout.py)
and the [script guide](../../../scripts/README.md#state-input-and-replay-follow-ups).
Use the configured LIBERO/MuJoCo 3.3.2 environment and a fresh output directory.
The loop follows the audited run. On 2026-11-01 its packaged `--self-only` entry
passed 10/10 self-replays in the existing environment, with exact action-prefix
checks and no formal episodes. This is bounded engineering acceptance, not a
new 400-target evaluation or clean-install validation; the historical outcomes
in this directory are unchanged.

Targets 10–49 did not participate in selecting actions. They had been used in
earlier normal evaluations and position summaries, so this is not a hidden test
set or a new-task generalization result. Replaying actions still uses the normal
low-level feedback controller. Full replay NPZ files remain outside Git;
their hashes and recorded audit are not a replacement for those files.

## 中文说明

十条动作在P2运行前已固定；`source_actions.json`保真导出原float32数组，
以冻结清单中的内容哈希核对。动作不裁剪、不延长，也不按新结果重选。
`outcomes.json`包含10个自回放和400个正式目标的全部结果、结束原因及原证据哈希。

目标10–49未参与动作选择，但曾用于旧正常评测和位置统计，不称隐藏测试集。
完整回放NPZ留在Git外；公开数据可重算成功率和区间，不能重做完整逐步审计。
打包入口沿用原回放循环，2026-11-01既有环境的`--self-only`自检为10/10，
动作前缀核对通过、正式回合为0；这是有界工程验收，不是400目标复测或干净安装验证。
本目录历史结果保持不变。
固定高层动作的执行仍有底层控制反馈，不能据此认定LeRobot π0的内部机制。
