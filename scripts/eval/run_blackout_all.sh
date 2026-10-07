#!/bin/bash
# 四个模型全涂黑:三个 LeRobot 模型分两条线并行(第二条错开启动,避免两个进程同时加载权重),OpenVLA 最后单独跑
source "$(dirname "$0")/../common.sh"; R=$SCRIPTS/eval/run_libero.sh
lane1() { WRAP=blackout BLACKOUT=all bash $R pi0_black_all 10 $CK_PI0 1 --policy.n_action_steps=5
          WRAP=blackout BLACKOUT=all bash $R pi05_black_all 10 $CK_PI05 1 --policy.n_action_steps=10; }
lane2() { sleep 180
          WRAP=blackout BLACKOUT=all bash $R smol2_black_all 10 $CK_SMOL2 1 "${SMOL2_ARGS[@]}"; }
lane1 & lane2 & wait
# OpenVLA 单独跑:它占约 14 GB 显存,和 π0.5 同时跑会超出 24 GB
BLACKOUT=all bash $SCRIPTS/eval/run_ovla.sh openvla_black_all 10
echo DONE > ${EMB_ROOT}/logs/eval/blackout_done.flag
