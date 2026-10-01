#!/bin/bash
# 用法: STATE_DROP_P=<p> bash run_train.sh <run_name> <steps> <batch_size> [额外 lerobot-train 参数...]
source "$(dirname "$0")/../common.sh"
conda activate smolvla
export HF_HUB_OFFLINE=1
RUN=$1; N=$2; B=$3; shift 3
W=${EMB_ROOT}/logs/train/$RUN; rm -rf $W; mkdir -p $W; cd $W
DS=$(ls -d ${EMB_ROOT}/cache/lerobot/lerobot/libero@* | head -1)
( while true; do nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits >> $W/gpu_mem.log; sleep 2; done ) & MON=$!
python $SCRIPTS/train/train_statedrop.py --policy.path=$CK_PI0 \
  --dataset.repo_id=lerobot/libero --dataset.root=$DS --dataset.video_backend=torchcodec \
  --policy.train_expert_only=true --policy.gradient_checkpointing=true --policy.dtype=bfloat16 \
  --policy.compile_model=false --policy.push_to_hub=false --policy.device=cuda \
  --batch_size=$B --steps=$N --log_freq=25 --num_workers=6 --seed=1000 \
  --wandb.enable=false --job_name=$RUN --output_dir=$W/out "$@" > $W/stdout.log 2>&1
echo "exit=$?" >> $W/stdout.log; kill $MON
echo "peak_gpu_MiB=$(sort -n $W/gpu_mem.log | tail -1)" >> $W/stdout.log
