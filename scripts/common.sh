# 各入口脚本共用:加载环境、定位仓库脚本目录、公开权重在 ${EMB_ROOT}/ckpt 下的位置(目录名 = 仓库名@commit)。
: "${EMB_ROOT:?请先 export EMB_ROOT=<工作目录>}"
# 先定位脚本目录,再加载 env.sh(后者可能改变工作目录)
SCRIPTS=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd) || exit 1
source "${EMB_ROOT}/env.sh" >/dev/null || exit 1
CK=${EMB_ROOT}/ckpt
CK_ACT=$CK/act_aloha_sim_transfer_cube_human@ba73b276_migrated
CK_DP=$CK/diffusion_pusht@84a7c231_migrated
CK_OVLA=$CK/openvla-7b-finetuned-libero-spatial@962318ce
CK_SMOL=$CK/HuggingFaceVLA__smolvla_libero@6721902b
CK_PI0=$CK/pi0_libero_finetuned_v044@45dcc8fc
CK_PI05=$CK/pi05_libero_finetuned_v044@8e174154
