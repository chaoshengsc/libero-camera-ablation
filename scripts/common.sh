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
# OpenPI 官方 pi0_libero 的 LeRobot 转换版,经 eval/adapt_openpi_pi0.py 注入官方归一化统计量与增量动作还原后的本地副本
CK_PI0_OPENPI=$CK/pi0_libero_base@98ac51b8_openpi
# 诊断用:同一转换版,改用权重文件里夹带的统计量、不加增量还原(adapt_openpi_pi0.py ... embedded)
CK_PI0_OPENPI_EMB=$CK/pi0_libero_base@98ac51b8_embedded
# OpenPI 原版服务端(scripts/openpi/serve_pi0_libero.py)的检查点、端口与口令文件
CK_OPENPI_PI0=$CK/openpi_pi0_libero
OPENPI_PORT=${OPENPI_PORT:-18765}
OPENPI_KEYFILE=${EMB_ROOT}/tmp/openpi_authkey
