# 公开评测数据与历史记录

[项目首页](../../README_CN.md) · [统计与图表](../../results/README_CN.md) · [换设备继续实验](../../docs/CONTINUE_CN.md)

本目录提供逐回合结果、配对见证和部分审计摘要，支持重算公开统计。结果JSON不是模型权重，也不代表完整录像、NPZ或模型输入张量已经公开。

| 分组 | 入口 | 范围 |
|---|---|---|
| 腕部主实验与主视角附加条件 | [s500/](s500/) · [11组配置](../../configs/camera_study_runs.json) | 各运行500回合，正常组与历史重复单列 |
| 四模型全黑与三模型早期扰动 | [研究覆盖与运行说明](../../docs/STUDY_MAP_CN.md) · [结果来源映射](../build.py) | 顶层及run2至run5包含早期运行，不与后期500初态混称 |
| 官方π0检查点／管线对照 | [official_pi0/](official_pi0/) · [匹配100初态表](../../results/official_pi0_matched100.csv) | 不同权重与管线，不作单因素归因 |
| 状态更新与固定动作检查 | [P1](state_feedback/README.md) · [P2](replay_holdout/README.md) | 公开结果与动作支持相应统计，完整逐步NPZ留在Git外 |
| 协议与来源审计 | [protocol_audit/](protocol_audit/README.md) | 来源关联、长度记录及权重身份／加载摘要，非完整原始工件 |
| 历史微调诊断 | [公开历史日志](../../docs/NOTES_CN.md) | 12份eval_ft* JSON为旧π0诊断；p05指状态置零概率0.5，不是π0.5模型；不纳入本次相机冻结 |

[207份冻结证据清单](../../results/freeze_20261109_v1.5.3.sha256)列出被校验的公开数据与结果文件。本说明页由Git提交固定，不回写旧清单。独立微调项目不属于这次更新。

## Public data and historical records

The table separates the 500-episode wrist/agent controls, early four-policy blackout and three-policy perturbations, official π0 controls, P1/P2, protocol audit and historical fine-tuning diagnostics. See the [English study map](../../docs/STUDY_MAP.md) and [continuation guide](../../docs/CONTINUE.md).

Public files support outcome statistics and selected audits, not full replay of every historical tensor/trajectory audit. Full recordings, NPZ, weights and gated tokenizers remain outside Git. The twelve historical eval_ft* files are old π0 state-drop diagnostics; p05 denotes probability 0.5, not the π0.5 model. They are excluded from the camera-evidence manifest and distinct from the separate current fine-tuning project.
