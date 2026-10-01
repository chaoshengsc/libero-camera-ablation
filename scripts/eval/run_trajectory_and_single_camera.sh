#!/bin/bash
# 记录末端轨迹 + 只涂黑一路相机,两条线并行
source "$(dirname "$0")/../common.sh"; R=$SCRIPTS/eval/run_libero.sh
export WRAP=probe
lane1() {
  BLACKOUT=none  bash $R traj_pi0_normal  10 $CK_PI0 1 --policy.n_action_steps=5
  BLACKOUT=none  bash $R traj_pi0_normal2 10 $CK_PI0 1 --policy.n_action_steps=5
  BLACKOUT=all   bash $R traj_pi0_black   10 $CK_PI0 1 --policy.n_action_steps=5
  BLACKOUT=agent bash $R traj_pi0_agent   10 $CK_PI0 1 --policy.n_action_steps=5
  BLACKOUT=wrist bash $R traj_pi0_wrist   10 $CK_PI0 1 --policy.n_action_steps=5
  BLACKOUT=wrist bash $R traj_smol_wrist  10 $CK_SMOL 1
}
lane2() {
  sleep 240
  BLACKOUT=none  bash $R traj_pi05_normal 10 $CK_PI05 1 --policy.n_action_steps=10
  BLACKOUT=agent bash $R traj_pi05_agent  10 $CK_PI05 1 --policy.n_action_steps=10
  BLACKOUT=wrist bash $R traj_pi05_wrist  10 $CK_PI05 1 --policy.n_action_steps=10
  BLACKOUT=agent bash $R traj_smol_agent  10 $CK_SMOL 1
}
lane1 & lane2 & wait
echo DONE > ${EMB_ROOT}/logs/eval/trajectory_done.flag
