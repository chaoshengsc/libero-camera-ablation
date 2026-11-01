#!/bin/bash
set -e
# 状态置零微调的全流程:测速定 batch → 两组训练(对照 p=0 / 状态置零 p=0.5)→ 各评测正常与全涂黑
# 用法: bash run_statedrop_pipeline.sh [steps]   (默认 3000,即 README 2.4 节的设置)
# 前置:lerobot/libero 数据集已在 ${EMB_ROOT}/cache/lerobot/lerobot/libero@<commit>(见 docs/INSTALL.md 第 4 节)
source "$(dirname "$0")/../common.sh"
N=${1:-3000}
L=${EMB_ROOT}/logs; T=$L/train; RT=$SCRIPTS/train/run_train.sh; RE=$SCRIPTS/eval/run_libero.sh; REP=$T/pipeline.log
reserve_pipeline "$T/.statedrop_pipeline.started" "$REP" "$T/pipeline_done.flag" \
  "$T/probe_bs16" "$T/probe_bs8" "$T/ft_p0" "$T/ft_p05" \
  "$L/eval/eval_ft_p0_normal" "$L/eval/eval_ft_p0_black" "$L/eval/eval_ft_p05_normal" "$L/eval/eval_ft_p05_black"
trap 'status=$?; if [ "$status" -ne 0 ]; then echo FAIL > "$T/pipeline_done.flag"; fi' EXIT
log() { echo "$(date '+%F %T') $*" >> "$REP"; }
if ! ls -d "$EMB_ROOT"/cache/lerobot/lerobot/libero@* >/dev/null 2>&1; then
  log "lerobot/libero dataset not found, pipeline stopped"; echo FAIL > "$T/pipeline_done.flag"; exit 1
fi
log "timing run started"

if STATE_DROP_P=0 bash "$RT" probe_bs16 150 16 --save_freq=100000; then B=16; PR=probe_bs16
else
  log "bs16 timing run failed: $(grep -aE "Error|error" "$T/probe_bs16/stdout.log" | tail -1 | cut -c1-150); trying bs8"
  if STATE_DROP_P=0 bash "$RT" probe_bs8 150 8 --save_freq=100000; then :; else
    status=$?
    log "bs8 failed too: $(grep -aE "Error|error" "$T/probe_bs8/stdout.log" | tail -1 | cut -c1-150); pipeline stopped"
    echo FAIL > "$T/pipeline_done.flag"; exit "$status"
  fi
  B=8; PR=probe_bs8
fi
SPS=$(grep -a "\[timing\]" "$T/$PR/stdout.log" | tail -1 | sed -E 's/.*avg ([0-9.]+)s.*/\1/')
WU=$(( N / 10 < 1000 ? N / 10 : 1000 ))
log "timing: bs=$B, ${SPS}s per step, $(grep -a peak_gpu "$T/$PR/stdout.log") -> $N steps per run (warmup $WU)"

for p in 0 0.5; do
  name=ft_p${p/./}; log "training $name started (STATE_DROP_P=$p)"
  if STATE_DROP_P=$p bash "$RT" "$name" "$N" "$B" --save_freq="$N" \
    --policy.scheduler_warmup_steps="$WU" --policy.scheduler_decay_steps="$N"; then
    log "$name training finished, $(grep -a peak_gpu "$T/$name/stdout.log")"
  else
    status=$?; log "$name training failed: $(grep -aE "Error|error" "$T/$name/stdout.log" | tail -1 | cut -c1-150)"
    exit "$status"
  fi
done

for p in 0 0.5; do
  name=ft_p${p/./}; C=$T/$name/out/checkpoints/last/pretrained_model
  if [ ! -d "$C" ]; then log "$name has no checkpoint, pipeline stopped"; exit 1; fi
  WRAP=probe BLACKOUT=none bash "$RE" eval_${name}_normal 10 "$C" 1 --policy.n_action_steps=5
  WRAP=probe BLACKOUT=all  bash "$RE" eval_${name}_black  10 "$C" 1 --policy.n_action_steps=5
  log "$name evaluation finished: normal $(grep -a "^exit=" "$L/eval/eval_${name}_normal/stdout.log"), black $(grep -a "^exit=" "$L/eval/eval_${name}_black/stdout.log")"
done
echo DONE > "$T/pipeline_done.flag"; log "pipeline finished"
