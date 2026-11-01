# 各入口脚本共用:加载环境、定位仓库脚本目录、公开权重在 ${EMB_ROOT}/ckpt 下的位置(目录名 = 仓库名@commit)。
: "${EMB_ROOT:?set it first: export EMB_ROOT=<working directory>}"
# 先定位脚本目录,再加载 env.sh(后者可能改变工作目录)
SCRIPTS=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd) || exit 1
source "${EMB_ROOT}/env.sh" >/dev/null || exit 1
CK=${EMB_ROOT}/ckpt
CK_ACT=$CK/act_aloha_sim_transfer_cube_human@ba73b276_migrated
CK_DP=$CK/diffusion_pusht@84a7c231_migrated
CK_OVLA=$CK/openvla-7b-finetuned-libero-spatial@962318ce
CK_SMOL=$CK/HuggingFaceVLA__smolvla_libero@6721902b
CK_SMOL2=$CK/lerobot__smolvla_libero@31d453f7
# lerobot/smolvla_libero 评测时需要的额外参数
SMOL2_ARGS=(--policy.n_action_steps=10 '--rename_map={"observation.images.image": "observation.images.camera1", "observation.images.image2": "observation.images.camera2"}')
CK_PI0=$CK/pi0_libero_finetuned_v044@45dcc8fc
CK_PI05=$CK/pi05_libero_finetuned_v044@8e174154
# 历史HF候选的本地适配副本:未通过与原生GCS权重的同源性核验;注入官方统计量及增量还原不使其成为官方转换版
CK_PI0_OPENPI=$CK/pi0_libero_base@98ac51b8_openpi
# 诊断用:同一HF候选,改用文件内统计量且不加增量还原(adapt_openpi_pi0.py ... embedded)
CK_PI0_OPENPI_EMB=$CK/pi0_libero_base@98ac51b8_embedded
# OpenPI 原版服务端(scripts/openpi/serve_pi0_libero.py)的检查点、端口与口令文件
CK_OPENPI_PI0=$CK/openpi_pi0_libero
OPENPI_PORT=${OPENPI_PORT:-18765}
OPENPI_KEYFILE=${EMB_ROOT}/tmp/openpi_authkey

# Extra CLI arguments must not redirect a run outside its reserved output.
reject_output_override() {
  local arg
  for arg in "$@"; do
    case "$arg" in --output_dir|--output_dir=*) echo "output_dir is managed by the run name" >&2; return 2 ;; esac
  done
}

# Atomically reserve an unused output directory; never remove an old run.
new_run_dir() {
  local kind=$1 name=$2
  case "$kind" in eval|train) ;; *) echo "unknown run kind: $kind" >&2; return 2 ;; esac
  case "$name" in ""|.|..|*[!a-zA-Z0-9_.-]*) echo "invalid run name: $name" >&2; return 2 ;; esac
  W=$EMB_ROOT/logs/$kind/$name
  mkdir -p -- "$EMB_ROOT/logs/$kind" || return
  mkdir -- "$W" || { echo "Cannot reserve output; choose an unused run name: $W" >&2; return 1; }
}

# Reserve the whole pipeline before launching either lane or writing shared logs.
reserve_pipeline() {
  local lock=$1 path
  shift
  for path in "$@"; do
    if [ -e "$path" ] || [ -L "$path" ]; then
      echo "Refusing to overwrite pipeline output: $path" >&2; return 1
    fi
  done
  mkdir -p -- "$(dirname "$lock")" || return
  mkdir -- "$lock" || { echo "Pipeline already reserved or unavailable: $lock" >&2; return 1; }
}

# Capture the command status before logging; a successful echo is not a run result.
run_logged() {
  local logfile=$1 status=0
  shift
  "$@" >> "$logfile" 2>&1 || status=$?
  if ! printf 'exit=%s\n' "$status" >> "$logfile"; then
    if [ "$status" -eq 0 ]; then status=1; fi
  fi
  return "$status"
}

# Bare wait ignores individual failures. Reap every owned child and report failure.
wait_for_jobs() {
  local pid status=0 child_status
  for pid in "$@"; do
    if wait "$pid"; then :; else
      child_status=$?
      if [ "$status" -eq 0 ]; then status=$child_status; fi
    fi
  done
  return "$status"
}
