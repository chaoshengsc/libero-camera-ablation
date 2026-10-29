#!/bin/bash
# 官方 π0(OpenPI pi0_libero)去掉视觉的实验,按 docs/NOTES.md 2026-10-28 的预先登记分段跑。
# 用法: bash run_official_pi0.sh <阶段>
# OpenPI 原版(先在 OpenPI 环境里起 scripts/openpi/serve_pi0_libero.py,端口与口令见下):
#   smoke     50 回合正常条件(每任务 5),只看日志里的证据,不报告
#   gate      500 回合正常条件(每任务 50),门槛 ≥ 92%
#   ablation  官方 π0 全涂黑 / 两路槽位都屏蔽 / 两路都冻结各 100 回合,LeRobot π0 两路槽位都屏蔽 100 回合
#   single    官方 π0 只屏蔽腕部 / 只屏蔽主视角各 100 回合(docs/NOTES.md 2026-10-29 预先登记)
#   freeze_wrist 官方 π0 只冻结腕部(整回合给第 1 帧真实画面,掩码为真)100 回合,与 ojx_drop_wrist 同一批初始状态
#   res360    官方 π0 改用 360 渲染(与 LeRobot 一侧相同):正常 / 全涂黑 / 两路槽位都屏蔽各 100 回合
#   replay    开环回放基线:官方 π0 在 360 渲染、正常条件下跑 100 回合并记录动作,再把动作原样回放到同一任务的其他初始状态
# LeRobot 转换版 lerobot/pi0_libero_base(冒烟不通过,留作记录):
#   conv_smoke  50 回合正常条件
#   conv_diag   三组对照,各 20 回合(每任务 2):a 夹带统计量且不加增量;b 增量用当前步状态;c 渲染分辨率 256
source "$(dirname "$0")/../common.sh"; R=$SCRIPTS/eval/run_libero.sh
export WRAP=probe
A=(--policy.n_action_steps=5)  # 与 OpenPI LIBERO 脚本的 replan_steps=5、以前 LeRobot π0 的运行一致
O=("${A[@]}" --env.observation_height=256 --env.observation_width=256)  # OpenPI 脚本 LIBERO_ENV_RESOLUTION=256
remote() { POLICY_SERVER=$OPENPI_PORT OPENPI_AUTHKEY=$(cat "$OPENPI_KEYFILE") "$@"; }
case "${1:?usage: run_official_pi0.sh smoke|gate|ablation|single|freeze_wrist|res360|replay|conv_smoke|conv_diag}" in
  smoke)    BLACKOUT=none remote bash $R ojx_smoke 5  $CK_PI0_OPENPI 1 "${O[@]}" ;;
  gate)     BLACKOUT=none remote bash $R ojx_none  50 $CK_PI0_OPENPI 1 "${O[@]}" ;;
  ablation)
    for m in all drop_all freeze; do BLACKOUT=$m remote bash $R ojx_$m 10 $CK_PI0_OPENPI 1 "${O[@]}"; done
    BLACKOUT=drop_all bash $R pi0_drop_all 10 $CK_PI0 1 "${A[@]}" ;;
  single)   for m in drop_wrist drop_agent; do BLACKOUT=$m remote bash $R ojx_$m 10 $CK_PI0_OPENPI 1 "${O[@]}"; done ;;
  freeze_wrist) BLACKOUT=freeze_wrist remote bash $R ojx_freeze_wrist 10 $CK_PI0_OPENPI 1 "${O[@]}" ;;
  res360)   for m in none all drop_all; do BLACKOUT=$m remote bash $R ojx360_$m 10 $CK_PI0_OPENPI 1 "${A[@]}"; done ;;
  replay)
    BLACKOUT=none remote bash $R ojx360_replay 10 $CK_PI0_OPENPI 1 "${A[@]}"
    W=$EMB_ROOT/logs/eval/ojx360_replay; conda activate smolvla
    MUJOCO_GL=egl python -I $SCRIPTS/analysis/replay_open_loop.py $W/traj.npz $W/out/eval_info.json 10 $W/replay.json ;;
  conv_smoke) BLACKOUT=none bash $R opi0_smoke 5 $CK_PI0_OPENPI 1 "${A[@]}" ;;
  conv_diag)
    BLACKOUT=none bash $R opi0_diag_a 2 $CK_PI0_OPENPI_EMB 1 "${A[@]}"
    DELTA_REF=step BLACKOUT=none bash $R opi0_diag_b 2 $CK_PI0_OPENPI 1 "${A[@]}"
    BLACKOUT=none bash $R opi0_diag_c 2 $CK_PI0_OPENPI 1 "${O[@]}" ;;
  *) echo "unknown stage: $1" >&2; exit 2 ;;
esac
