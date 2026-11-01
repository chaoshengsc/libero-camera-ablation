#!/bin/bash
set -e
# Diffusion Policy · PushT,500 回合
source "$(dirname "$0")/../common.sh"
conda activate lerobot
new_run_dir eval dp_pusht_500
cd "$W"
run_logged "$W/stdout.log" lerobot-eval --policy.path="$CK_DP" --policy.device=cuda \
  --env.type=pusht --eval.n_episodes=500 --eval.batch_size=50 --eval.use_async_envs=false \
  --seed=1000 --output_dir="$W/out"
