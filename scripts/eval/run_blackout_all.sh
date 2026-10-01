#!/bin/bash
# 四个模型全涂黑,两条线并行(第二条错开启动,避免两个进程同时加载权重)
source "$(dirname "$0")/../common.sh"; R=$SCRIPTS/eval/run_libero.sh
lane1() { WRAP=blackout BLACKOUT=all bash $R pi0_black_all 10 $CK_PI0 1 --policy.n_action_steps=5
          WRAP=blackout BLACKOUT=all bash $R pi05_black_all 10 $CK_PI05 1 --policy.n_action_steps=10; }
lane2() { sleep 180
          WRAP=blackout BLACKOUT=all bash $R smolvla_black_all 10 $CK_SMOL 1
          BLACKOUT=all bash $SCRIPTS/eval/run_ovla.sh openvla_black_all 10; }
lane1 & lane2 & wait
echo DONE > ${EMB_ROOT}/logs/eval/blackout_done.flag
