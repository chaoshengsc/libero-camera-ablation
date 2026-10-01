#!/bin/bash
# 方向 3 全自动流水线:测速 → 自动定步数 → 两组训练(对照 p=0 / 状态置零 p=0.5)→ 各评测正常与全涂黑
source "$(dirname "$0")/../common.sh"
L=${EMB_ROOT}/logs; T=$L/train; RT=$SCRIPTS/train/run_train.sh; RE=$SCRIPTS/eval/run_libero.sh; mkdir -p $T; REP=$T/pipeline.log
log() { echo "$(date '+%F %T') $*" >> $REP; }
log "流水线已排队,等待方向 1/2 完成与数据集下载"
until [ -f $L/eval/C_done.flag ] && grep -q "^DONE" $L/dl_libero_ds.log; do sleep 60; done
log "前置条件满足,开始测速"

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
N=$(python3 -c "s=float('$SPS'); n=int(3.5*3600/s)//100*100; print(max(500, min(10000, n)))")
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
