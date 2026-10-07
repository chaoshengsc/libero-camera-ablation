#!/bin/bash
# 温和扰动:加噪声 / 冻结画面 × π0、π0.5、SmolVLA,两条线并行(第二条错开启动)
source "$(dirname "$0")/../common.sh"; R=$SCRIPTS/eval/run_libero.sh
export WRAP=probe
lane1() {
  for m in noise freeze; do
    BLACKOUT=$m bash $R pert_pi0_$m  10 $CK_PI0  1 --policy.n_action_steps=5
    BLACKOUT=$m bash $R pert_pi05_$m 10 $CK_PI05 1 --policy.n_action_steps=10
  done
}
lane2() { sleep 240
  for m in noise freeze; do BLACKOUT=$m bash $R pert_smol2_$m 10 $CK_SMOL2 1 "${SMOL2_ARGS[@]}"; done
}
lane1 & lane2 & wait
