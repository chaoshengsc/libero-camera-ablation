#!/bin/bash
# 用法: [WRAP=none|blackout|probe] [BLACKOUT=...] bash run_libero.sh <run_name> <n_episodes_per_task> <ckpt_dir> <batch_size> [额外 lerobot-eval 参数...]
#   WRAP=none(默认)  直接跑 lerobot-eval
#   WRAP=blackout    经 eval_blackout.py 涂黑相机画面(BLACKOUT=all|agent|wrist;实验 B 用)
#   WRAP=probe       经 eval_probe.py 涂黑并记录末端轨迹到 <输出目录>/traj.npz(BLACKOUT=none|all|agent|wrist)
source "$(dirname "$0")/../common.sh"
conda activate smolvla
export HF_HUB_OFFLINE=1   # 权重、分词器、LIBERO 素材都已在本地
RUN=$1; N=$2; C=$3; B=$4; shift 4
W=${EMB_ROOT}/logs/eval/$RUN; rm -rf $W; mkdir -p $W; cd $W
case "${WRAP:-none}" in
  none)     CMD=(lerobot-eval) ;;
  blackout) CMD=(python $SCRIPTS/eval/eval_blackout.py) ;;
  probe)    CMD=(python $SCRIPTS/eval/eval_probe.py); export TRAJ_OUT=$W/traj.npz ;;
  *) echo "未知 WRAP=$WRAP" >&2; exit 2 ;;
esac
echo "args: $*" > $W/stdout.log
"${CMD[@]}" --policy.path=$C --policy.device=cuda --env.type=libero --env.task=libero_spatial \
  --eval.batch_size=$B --eval.n_episodes=$N --seed=1000 --output_dir=$W/out "$@" >> $W/stdout.log 2>&1
echo "exit=$?" >> $W/stdout.log
