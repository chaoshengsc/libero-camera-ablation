#!/bin/bash
# Diffusion Policy · PushT,500 回合
source "$(dirname "$0")/../common.sh"
conda activate lerobot
W=${EMB_ROOT}/logs/eval/dp_pusht_500; rm -rf $W; mkdir -p $W; cd $W
lerobot-eval --policy.path=$CK_DP --policy.device=cuda \
  --env.type=pusht --eval.n_episodes=500 --eval.batch_size=50 --eval.use_async_envs=false \
  --seed=1000 --output_dir=$W/out > $W/stdout.log 2>&1
echo "exit=$?" >> $W/stdout.log
