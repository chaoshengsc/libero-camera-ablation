#!/bin/bash
# ACT · ALOHA Transfer Cube,500 回合
source "$(dirname "$0")/../common.sh"
conda activate lerobot; cd ${EMB_ROOT}
lerobot-eval --policy.path=$CK_ACT --policy.device=cuda --env.type=aloha --env.task=AlohaTransferCube-v0 \
  --eval.n_episodes=500 --eval.batch_size=50 --eval.use_async_envs=false --seed=1000 \
  --output_dir=${EMB_ROOT}/logs/eval/act_cube_500 > ${EMB_ROOT}/logs/act_500.log 2>&1
echo "exit=$?" >> ${EMB_ROOT}/logs/act_500.log
