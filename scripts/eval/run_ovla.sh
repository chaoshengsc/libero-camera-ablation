#!/bin/bash
# 用法: [BLACKOUT=all] bash run_ovla.sh <run_name> <num_trials_per_task> [seed]
#   BLACKOUT=all 时经 openvla_blackout.py 把送进模型的图像换成全黑
source "$(dirname "$0")/../common.sh"
conda activate openvla
U="usage: run_ovla.sh <run_name> <num_trials_per_task> [seed]"
RUN=${1:?$U}; N=${2:?$U}; SEED=${3:-7}
case "${BLACKOUT:-}" in ""|all) ;; *) echo "unknown BLACKOUT=$BLACKOUT (only 'all' is supported)" >&2; exit 2 ;; esac
W=${EMB_ROOT}/logs/eval/$RUN; rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1
export PYTHONPATH=${EMB_ROOT}/src/openvla
PY=${EMB_ROOT}/src/openvla/experiments/robot/libero/run_libero_eval.py
[ "$BLACKOUT" = all ] && PY=$SCRIPTS/eval/openvla_blackout.py
python $PY \
  --model_family openvla \
  --pretrained_checkpoint "$CK_OVLA" \
  --task_suite_name libero_spatial --center_crop True \
  --num_trials_per_task $N --seed $SEED --local_log_dir $W/logs > $W/stdout.log 2>&1
echo "exit=$?" >> $W/stdout.log
