#!/bin/bash
set -e
# ACT · ALOHA Transfer Cube,500 回合
source "$(dirname "$0")/../common.sh"
conda activate lerobot
new_run_dir eval act_cube_500
cd "$W"
run_logged "$W/stdout.log" lerobot-eval --policy.path="$CK_ACT" --policy.device=cuda --env.type=aloha --env.task=AlohaTransferCube-v0 \
  --eval.n_episodes=500 --eval.batch_size=50 --eval.use_async_envs=false --seed=1000 \
  --output_dir="$W/out"
