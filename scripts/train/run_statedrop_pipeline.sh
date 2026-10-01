#!/bin/bash
# 状态置零微调的全流程:测速定 batch → 两组训练(对照 p=0 / 状态置零 p=0.5)→ 各评测正常与全涂黑
# 用法: bash run_statedrop_pipeline.sh [steps]   (默认 3000,即 README 2.4 节的设置)
# 前置:lerobot/libero 数据集已在 ${EMB_ROOT}/cache/lerobot/lerobot/libero@<commit>(见 docs/INSTALL.md 第 4 节)
source "$(dirname "$0")/../common.sh"
N=${1:-3000}
L=${EMB_ROOT}/logs; T=$L/train; RT=$SCRIPTS/train/run_train.sh; RE=$SCRIPTS/eval/run_libero.sh; mkdir -p $T; REP=$T/pipeline.log
log() { echo "$(date '+%F %T') $*" >> $REP; }
if ! ls -d ${EMB_ROOT}/cache/lerobot/lerobot/libero@* >/dev/null 2>&1; then
  log "找不到 lerobot/libero 数据集,流水线停止"; echo FAIL > $T/pipeline_done.flag; exit 1
fi
log "开始测速"

STATE_DROP_P=0 bash $RT probe_bs16 150 16 --save_freq=100000
if grep -q "^exit=0" $T/probe_bs16/stdout.log; then B=16; PR=probe_bs16
else
  log "bs16 测速失败:$(grep -aE "Error|error" $T/probe_bs16/stdout.log | tail -1 | cut -c1-150);改试 bs8"
  STATE_DROP_P=0 bash $RT probe_bs8 150 8 --save_freq=100000
  if ! grep -q "^exit=0" $T/probe_bs8/stdout.log; then
    log "bs8 也失败:$(grep -aE "Error|error" $T/probe_bs8/stdout.log | tail -1 | cut -c1-150);流水线停止"
    echo FAIL > $T/pipeline_done.flag; exit 1
  fi
  B=8; PR=probe_bs8
fi
SPS=$(grep -a "\[timing\]" $T/$PR/stdout.log | tail -1 | sed -E 's/.*avg ([0-9.]+)s.*/\1/')
WU=$(( N / 10 < 1000 ? N / 10 : 1000 ))
log "测速结果:bs=$B,每步 ${SPS}s,$(grep -a peak_gpu $T/$PR/stdout.log) → 每组训练 $N 步(预热 $WU)"

for p in 0 0.5; do
  name=ft_p${p/./}; log "开始训练 $name(STATE_DROP_P=$p)"
  STATE_DROP_P=$p bash $RT $name $N $B --save_freq=$N \
    --policy.scheduler_warmup_steps=$WU --policy.scheduler_decay_steps=$N
  if grep -q "^exit=0" $T/$name/stdout.log; then log "$name 训练完成,$(grep -a peak_gpu $T/$name/stdout.log)"
  else log "$name 训练失败:$(grep -aE "Error|error" $T/$name/stdout.log | tail -1 | cut -c1-150)"; fi
done

for p in 0 0.5; do
  name=ft_p${p/./}; C=$T/$name/out/checkpoints/last/pretrained_model
  if [ ! -d "$C" ]; then log "$name 没有检查点,跳过评测"; continue; fi
  WRAP=probe BLACKOUT=none bash $RE eval_${name}_normal 10 $C 1 --policy.n_action_steps=5
  WRAP=probe BLACKOUT=all  bash $RE eval_${name}_black  10 $C 1 --policy.n_action_steps=5
  log "$name 评测完成:正常 $(grep -a "^exit=" $L/eval/eval_${name}_normal/stdout.log),涂黑 $(grep -a "^exit=" $L/eval/eval_${name}_black/stdout.log)"
done
echo DONE > $T/pipeline_done.flag; log "流水线全部完成"
