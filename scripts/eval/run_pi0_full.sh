#!/bin/bash
# π0:先 2 回合冒烟测试,通过后跑完整 500 回合
source "$(dirname "$0")/../common.sh"; R=$SCRIPTS/eval/run_libero.sh
bash $R pi0_smoke 2 $CK_PI0 1 --policy.n_action_steps=5
grep -q "^exit=0" ${EMB_ROOT}/logs/eval/pi0_smoke/stdout.log || exit 1
bash $R pi0_spatial_500 50 $CK_PI0 1 --policy.n_action_steps=5
