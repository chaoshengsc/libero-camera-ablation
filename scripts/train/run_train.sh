#!/bin/bash
# 用法: STATE_DROP_P=<p> bash run_train.sh <run_name> <steps> <batch_size> [额外 lerobot-train 参数...]
source "$(dirname "$0")/../common.sh"
conda activate smolvla
export HF_HUB_OFFLINE=1
U="用法: run_train.sh <run_name> <steps> <batch_size> [额外参数...]"
RUN=${1:?$U}; N=${2:?$U}; B=${3:?$U}; shift 3
W=${EMB_ROOT}/logs/train/$RUN; rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1
DS=$(ls -d ${EMB_ROOT}/cache/lerobot/lerobot/libero@* 2>/dev/null | head -1)
[ -n "$DS" ] || { echo "找不到 lerobot/libero 数据集(见 docs/INSTALL.md 第 4 节)" > $W/stdout.log; echo "exit=1" >> $W/stdout.log; exit 1; }
( while true; do nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits >> $W/gpu_mem.log; sleep 2; done ) & MON=$!
python $SCRIPTS/train/train_statedrop.py --policy.path=$CK_PI0 \
  --dataset.repo_id=lerobot/libero --dataset.root=$DS --dataset.video_backend=torchcodec \
  --policy.train_expert_only=true --policy.gradient_checkpointing=true --policy.dtype=bfloat16 \
  --policy.compile_model=false --policy.push_to_hub=false --policy.device=cuda \
  --batch_size=$B --steps=$N --log_freq=25 --num_workers=6 --seed=1000 \
  --wandb.enable=false --job_name=$RUN --output_dir=$W/out "$@" > $W/stdout.log 2>&1
echo "exit=$?" >> $W/stdout.log; kill $MON
echo "peak_gpu_MiB=$(sort -n $W/gpu_mem.log | tail -1)" >> $W/stdout.log
