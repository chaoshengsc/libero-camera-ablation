#!/bin/bash
# 实验 A:π0 的 n_action_steps 取 10 / 50(5 即主评测的设置)
source "$(dirname "$0")/../common.sh"; R=$SCRIPTS/eval/run_libero.sh
for k in 10 50; do bash $R pi0_nas$k 10 $CK_PI0 1 --policy.n_action_steps=$k; done
