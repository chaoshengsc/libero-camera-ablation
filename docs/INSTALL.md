# Installation

[中文](INSTALL_CN.md) · [Project overview](../README.md) · [Docs & data](README.md)

The original environment setup follows recorded workstation steps (Ubuntu 24.04, RTX A5000, driver 570, no sudo, no apt). Reconstructed additions are identified separately.
**They have not been re-run from scratch on a clean machine.** Version numbers match `constraints-*.txt`.

For the native **OpenPI/JAX π0 server plus LeRobot client**, use the separate [OpenPI installation and reproduction guide](OPENPI.md). It records the additional environment, pinned upstream lock, native checkpoint, tokenizer cache and acceptance steps; the three environments below do not include that server.

## 0. Working directory and Miniforge

```bash
git clone https://github.com/chaoshengsc/libero-camera-ablation.git && cd libero-camera-ablation
export REPO=$PWD                        # location of this repo; later commands use it to find scripts
export EMB_ROOT=/path/to/workdir        # a directory on a large disk: environments, caches, checkpoints and logs all go here
mkdir -p $EMB_ROOT/{home,tmp,cache,envs,src,ckpt,logs/pip}
cp env/env.sh.example $EMB_ROOT/env.sh
cp env/condarc.example $EMB_ROOT/home/.condarc   # replace ${EMB_ROOT} inside with the actual path
cp env/constraints-*.txt $EMB_ROOT/logs/pip/
```

`env.sh` redirects HOME, caches and temporary directories to `$EMB_ROOT`. To isolate this project from others on the same machine, add `export EMB_STRICT=1`: `env.sh` then refuses to load unless `$EMB_ROOT` is its own mount point with mode 700.
Install Miniforge (this project used 26.7.2) to `$EMB_ROOT/miniforge3` without running `conda init`. After that, run `source $EMB_ROOT/env.sh` first in every terminal.

Clone the sources into `$EMB_ROOT/src/` at these pinned versions:

| Repository | Version |
|---|---|
| huggingface/lerobot | v0.6.1 (7e241bd6) |
| openvla/openvla | c8f03f48 |
| Lifelong-Robot-Learning/LIBERO | 8f1084e3 |

```bash
cd $EMB_ROOT/src
git clone https://github.com/huggingface/lerobot.git && git -C lerobot checkout 7e241bd6
git clone https://github.com/openvla/openvla.git && git -C openvla checkout c8f03f48
git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git && git -C LIBERO checkout 8f1084e3
```

## 1. `lerobot` environment (ACT, Diffusion Policy)

```bash
conda create -y -n lerobot python=3.12 git curl tmux cmake "ffmpeg=7.1.1"
conda activate lerobot && cd $EMB_ROOT/src/lerobot
C=$EMB_ROOT/logs/pip/constraints-torch.txt
pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu128 "torch==2.11.0+cu128" "torchvision==0.26.0+cu128"
pip install --only-binary=:all: -c $C -e ".[aloha]"
# Diffusion Policy on PushT: install gym-pusht without dependencies so it does not replace opencv-python-headless
pip install --only-binary=:all: -c $C --no-deps "gym-pusht==0.1.6"
pip install --only-binary=:all: -c $C "pymunk>=6.6.0,<7.0.0" "pygame>=2.5.2" "scikit-image>=0.22.0" "shapely>=2.0.3"
pip install --only-binary=:all: -c $C "diffusers>=0.38.0,<0.40.0"
```

- torch has to come from the cu128 index: the default torch on PyPI is built for CUDA 13, which driver 570 does not support.
- ffmpeg is pinned to 7.1.1: torchcodec 0.11 does not support ffmpeg 9.

Sanity check: `python $REPO/scripts/checks/torch_check.py`. The same directory also has `egl_smoke.py` and `codec_check.py`.

## 2. `openvla` environment

```bash
conda create -y -n openvla python=3.10.13 git ninja
conda activate openvla
C=$EMB_ROOT/logs/pip/constraints-ovla.txt
pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu121 torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0
(cd $EMB_ROOT/src/openvla && pip install -c $C -e .)
# flash-attn: install the official prebuilt wheel (building from source requires CUDA_HOME)
pip install -c $C "https://github.com/Dao-AILab/flash-attention/releases/download/v2.5.5/flash_attn-2.5.5+cu122torch2.2cxx11abiFALSE-cp310-cp310-linux_x86_64.whl"
(cd $EMB_ROOT/src/LIBERO && pip install --no-deps -e . --config-settings editable_mode=compat)
pip install -c $C -r $EMB_ROOT/src/openvla/experiments/robot/libero/libero_requirements.txt
pip install --only-binary=:all: -c $C "mujoco==3.3.2" "tensorflow-metadata==1.17.1" "protobuf==4.21.12"
```

- MuJoCo ≥ 3.3.3 makes LIBERO render darker (LIBERO issue #88), so it is pinned to 3.3.2.
- LIBERO must be installed with `editable_mode=compat`; otherwise it cannot be imported after installation.

## 3. `smolvla` environment (SmolVLA, π0, π0.5; shared by evaluation and training)

```bash
conda create -y -n smolvla python=3.12 git cmake "ffmpeg=7.1.1"
conda activate smolvla && cd $EMB_ROOT/src/lerobot
pip install --only-binary=:all: --index-url https://download.pytorch.org/whl/cu128 "torch==2.11.0+cu128" "torchvision==0.26.0+cu128"
CMAKE_POLICY_VERSION_MINIMUM=3.5 pip install --prefer-binary -c $EMB_ROOT/logs/pip/constraints-smolvla.txt -e ".[smolvla,libero]"
```

- `CMAKE_POLICY_VERSION_MINIMUM=3.5` lets `egl_probe` compile with recent CMake.
- This environment cannot be merged with `lerobot`: it needs mujoco 3.3.2, while the dm_control used by ACT requires ≥ 3.8.1.

## 4. Checkpoints

Download with `hf download <repo> --revision <commit> --local-dir $EMB_ROOT/ckpt/<dir>`. Directory names are listed in `scripts/common.sh` (format: `repo name@first 8 characters of the commit`); `results/reproduction.csv` also uses short revisions. The base-model preparation below uses a full revision. For example:

```bash
hf download lerobot/pi05_libero_finetuned_v044 --revision 8e174154 --local-dir $EMB_ROOT/ckpt/pi05_libero_finetuned_v044@8e174154
```

- **ACT and Diffusion Policy** checkpoints are in the old format and have to be migrated first (DP goes through `migrate_tuplefix.py`, a wrapper that fixes a list/tuple decoding problem):
  ```bash
  conda activate lerobot
  # ACT: use the migration script that ships with LeRobot
  CK=$EMB_ROOT/ckpt/act_aloha_sim_transfer_cube_human@ba73b276
  python $EMB_ROOT/src/lerobot/src/lerobot/processor/migrate_policy_normalization.py --pretrained-path $CK --output-dir ${CK}_migrated
  # Diffusion Policy: run only this one (the wrapper calls the migration script above internally)
  CK=$EMB_ROOT/ckpt/diffusion_pusht@84a7c231
  python $REPO/scripts/eval/migrate_tuplefix.py --pretrained-path $CK --output-dir ${CK}_migrated
  ```
- **LeRobot π0 and π0.5** use the tokenizer from the gated repository `google/paligemma-3b-pt-224`: request access on Hugging Face yourself, download the tokenizer files,
  then set `tokenizer_name` in the checkpoint's `policy_preprocessor.json` to the local path. This repo does not distribute the tokenizer.
- **Native OpenPI π0** uses its original Orbax checkpoint and a separate GCS tokenizer cache; follow [the OpenPI guide](OPENPI.md#3-native-weights-normalization-and-tokenizer), not the LeRobot checkpoint/tokenizer procedure above.
- **Training data for the state-zeroing fine-tune**: the `lerobot/libero` dataset (about 1.9 GB), placed at `$EMB_ROOT/cache/lerobot/lerobot/libero@<commit>`.

### 4.1 Prepare for offline evaluation

`run_libero.sh` sets `HF_HUB_OFFLINE=1`. Prepare the selected policy and its local dependencies, plus LIBERO assets; downloading a SmolVLA policy does not cache its base model. **The base-model download block below applies only to SmolVLA; P1 and native OpenPI do not need it.** These additional steps are reconstructed from recorded versions and source. **No download, model load or clean-machine acceptance was performed during this update.**

SmolVLA reproduction uses `HuggingFaceTB/SmolVLM2-500M-Video-Instruct@7b375e1b73b11138ff12fe22c8f2822d8fe03467`. The public policy sets `load_vlm_weights=True`, so initialization still reads base-model weights and its processor; configuration files alone are insufficient. Sources: [policy config](https://huggingface.co/lerobot/smolvla_libero/blob/31d453f7/config.json) and [pinned base-model files](https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct/tree/7b375e1b73b11138ff12fe22c8f2822d8fe03467).

**Downloads and writes cache files.** Run from any directory on the Linux workstation after installing the environments, with `EMB_ROOT` set. Keep `HF_HUB_CACHE` set for subsequent evaluations. Select the required weights/configuration without ONNX variants:

```bash
source "$EMB_ROOT/env.sh"
conda activate smolvla
export HF_HUB_CACHE="$HF_HOME/hub"
(
  set -e
  export BASE_REPO=HuggingFaceTB/SmolVLM2-500M-Video-Instruct
  export BASE_REV=7b375e1b73b11138ff12fe22c8f2822d8fe03467
  hf download "$BASE_REPO" --revision "$BASE_REV" \
    --include '*.json' '*.txt' '*.model' model.safetensors
  python - <<'PY'
import os
from pathlib import Path

from huggingface_hub import hf_hub_download

repo_id, revision = os.environ["BASE_REPO"], os.environ["BASE_REV"]
cache = Path(os.environ["HF_HUB_CACHE"])
model = cache / ("models--" + repo_id.replace("/", "--"))
snapshot = model / "snapshots" / revision
required = ("config.json", "model.safetensors", "tokenizer.json",
            "tokenizer_config.json", "preprocessor_config.json", "processor_config.json")
if not all((snapshot / name).is_file() for name in required):
    raise SystemExit("Incomplete pinned base-model snapshot; stop")
ref = model / "refs/main"
if ref.exists() or ref.is_symlink():
    if ref.read_text().strip() != revision:
        raise SystemExit("Existing main cache reference differs; do not overwrite it")
else:
    ref.parent.mkdir(parents=True, exist_ok=True)
    with ref.open("x") as output:
        output.write(revision)
for name in required:
    path = hf_hub_download(repo_id, name, revision="main",
                           cache_dir=str(cache), local_files_only=True)
    if Path(path).parent.name != revision:
        raise SystemExit("Offline lookup resolved to a different revision")
print("Pinned base-model files resolve offline; no model loaded")
PY
)
```

A commit download does not create `refs/main`; this LeRobot version requests the base by repository name without a revision. The step pins **this project's cached main alias** to the downloaded commit, without changing the remote branch. A differing existing alias stops preparation; old cache files are not deleted or overwritten. Audit their provenance or prepare a separate isolated cache instead of forcing the pointer to pass.

Expect `Pinned base-model files resolve offline; no model loaded`. This checks file presence and offline resolution, not weight-content hashes, model inference or success rates. In each new evaluation terminal, load `env.sh` and set `HF_HUB_CACHE="$HF_HOME/hub"` again. Resolve missing files at the fixed revision rather than disabling offline mode and mixing versions.

LeRobot π0/π0.5 still need the local tokenizer setup above; native OpenPI needs its separate GCS cache. LIBERO's BDDL, initial-state and asset directories must also be local and match the pinned `hf-libero`/LIBERO source configuration. **Evaluation alone does not require the `lerobot/libero` training dataset.** Then choose the [minimal camera entry](../scripts/README.md#minimal-camera-evaluation) or [P1 launch steps](../scripts/README.md#p1-launch-steps-for-an-authorized-independent-repeat).

### 4.2 Prepare LIBERO simulation assets

The [hf-libero 0.1.4 source](https://github.com/huggingface/LIBERO/blob/8561c60eea2fb93096146f240194649df73d8b1e/libero/libero/utils/download_utils.py) gets meshes/textures from the **dataset** repository [lerobot/libero-assets](https://huggingface.co/datasets/lerobot/libero-assets/tree/0b3ea86be5fe169d0fd036ae63d1070ec09e90f6). This is separate from policy weights and training demonstrations. Its default destination is `$HOME/.cache/libero/assets`; after loading this project's `env.sh`, that is `$EMB_ROOT/home/.cache/libero/assets`, outside `HF_HOME`.

**Only for a new, empty asset cache; downloads about 422 MB.** Run on the Linux workstation from any directory after sections 0–3, with `REPO` and `EMB_ROOT` set. The block pins a published asset snapshot for future setup; it does not establish which asset revision was present in historical experiments. It exclusively creates the destination and stops on existing directories/files/links. A failed download leaves its partial directory for inspection; do not delete or overwrite it to force a retry. `HF_HUB_OFFLINE=0` applies only to the explicit preparation command, not later evaluation.

```bash
source "$EMB_ROOT/env.sh"
conda activate smolvla
(
  set -e
  HF_HUB_OFFLINE=0 python - <<'ASSETS'
from importlib import metadata
from pathlib import Path

from huggingface_hub import snapshot_download

dist = metadata.distribution("hf-libero")
if dist.version != "0.1.4":
    raise SystemExit("Stop: expected hf-libero 0.1.4")
package = Path(dist.locate_file("libero/libero"))
if (package / "assets").exists():
    raise SystemExit("Packaged assets take priority; inspect them before preparing a cache")
target = Path.home() / ".cache/libero/assets"
target.mkdir(parents=True, exist_ok=False)
snapshot_download(
    repo_id="lerobot/libero-assets", repo_type="dataset",
    revision="0b3ea86be5fe169d0fd036ae63d1070ec09e90f6",
    local_dir=str(target),
)
ASSETS
  python "$REPO/scripts/checks/libero_assets_check.py"
)
```

Expected output ends with `LIBERO Spatial files and required asset directories present`. For an already prepared installation, skip the download block and run only:

```bash
source "$EMB_ROOT/env.sh"
conda activate smolvla
python "$REPO/scripts/checks/libero_assets_check.py"
```

This read-only check requires ten nonempty Spatial BDDL and initial-state files in the installed package, plus nonempty `articulated_objects`, `stable_scanned_objects`, `turbosquid_objects`, `stable_hope_objects` and `scenes` asset directories. It imports neither LIBERO nor a simulator. Missing packages, wrong versions or missing/empty directories return nonzero. Packaged `libero/libero/assets` takes priority over the home cache, so an incomplete packaged directory must be inspected even if the cache is complete. The check does not verify every mesh/hash, custom LIBERO configuration, rendering or clean-machine execution.

On LIBERO's first import, its configuration may ask for a custom **training dataset** path; answer `n` to retain package defaults when only evaluating. Keep BDDL/init paths consistent with the installed version; inspect an existing custom configuration rather than replacing it. OpenVLA uses the separately pinned original LIBERO clone from section 0; its bundled assets/configuration are separate from this hf-libero cache. Native OpenPI's client uses the `smolvla`/hf-libero environment above. This documentation update performs no asset download or simulation.

## 5. Running evaluations

```bash
bash "$REPO/scripts/eval/run_act.sh"  # ACT, 500 episodes, about 17 minutes
CK="$EMB_ROOT/ckpt/pi05_libero_finetuned_v044@8e174154"
RUN=pi05_spatial_check
bash "$REPO/scripts/eval/run_libero.sh" "$RUN" 50 "$CK" 1 \
  --policy.n_action_steps=10
python3 "$REPO/scripts/analysis/summarize_eval.py" "$RUN"
```

Outputs go to `$EMB_ROOT/logs/eval/<run_name>/`; a last line of `exit=0` in `stdout.log` means the run finished normally. Entry points for each experiment are listed in `scripts/README.md`.

`CK` must be the prepared checkpoint; choose an unused `RUN`. The LIBERO command runs 50 episodes per task, 500 total. For the bounded ten-episode camera check, use [the minimal example](../scripts/README.md#minimal-camera-evaluation) instead.

For result registration, required pairing/hash records and the complete regeneration sequence, follow [the script guide](../scripts/README.md#existing-data-analysis-and-figures). Copying a JSON file alone does not register a run in the dashboard.

## 6. Official OpenPI π0

Continue with [the dedicated guide](OPENPI.md): recorded versions → separate JAX environment → native weights/cache → configuration-only client → local server/client → staged acceptance. Its commands document the historical pipeline and a reconstructed setup recipe; this documentation update did not reinstall dependencies or run new experiments. Recovery experiments and P3 remain paused.

## 7. Validation scope

On 2026-11-01, bounded entry checks ran in the **existing** Ubuntu/RTX A5000 client environment, reusing installed packages, weights and cached assets. No installation or weight/tokenizer download was performed.

| Entry | Actual check | Scope |
|---|---|---|
| Minimal all-black camera example | 10 episodes, process exit 0, two black camera inputs, finite trajectories and all ten initial-frame hashes matching the earlier study | Engineering acceptance; excluded from formal result tables |
| Packaged P2 `--self-only` | 10/10 self-replays, exact action prefixes, ten original initial-state matches, zero formal episodes | Self gate and output artifacts; no new 400-target result |
| Invalid input / existing outputs | Nonzero exits; existing failed and successful artifacts unchanged | Runtime failure propagation and overwrite protection |

The installed `hf-libero` 0.1.4 supplies BDDL/init files in its package. In this installation its separate mesh/texture assets resolve through `Path.home() / ".cache/libero/assets"`, which `env.sh` places at `$EMB_ROOT/home/.cache/libero/assets`. The `articulated_objects`, `stable_scanned_objects`, `turbosquid_objects`, `stable_hope_objects` and `scenes` directories were present before evaluation; no asset download was needed. Setting `HF_HOME` alone does not prepare this separate directory.

These checks do not establish clean-machine installation acceptance. The full P1 pipeline, P2 formal stage and native OpenPI server were not rerun. Historical formal outcomes and intervals are unchanged; the checks and a corrected stdout-parsing failure are recorded in [the experiment log](NOTES.md#bounded-entry-point-acceptance-and-v15-snapshot-2026-11-01). Recovery experiments and P3 remain paused.
