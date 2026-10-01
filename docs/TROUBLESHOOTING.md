# Troubleshooting

English | [中文](TROUBLESHOOTING_CN.md)

Organised as symptom → cause → fix. Everything here was actually hit during this reproduction.

## Installation

| Symptom | Cause | Fix |
|---|---|---|
| After installing torch, `cuda.is_available()` is False or a CUDA version error appears | The default torch on PyPI is built for CUDA 13, which driver 570 does not support | Install from `https://download.pytorch.org/whl/cu128` and pin torch with a constraints file |
| Video decoding errors (torchcodec) | torchcodec 0.11 does not support ffmpeg 9 | Pin `ffmpeg=7.1.1` in conda |
| Installing `flash-attn` asks for `CUDA_HOME` | Building from source needs the full CUDA toolchain | Install the prebuilt wheel from the official releases |
| `import libero` fails after `pip install -e .` in LIBERO | The editable install mode of recent setuptools is incompatible with its package layout | `pip install -e . --config-settings editable_mode=compat` |
| `pip check` reports a protobuf conflict in the OpenVLA environment | tensorflow-metadata and protobuf constrain each other's versions | `protobuf==4.21.12` + `tensorflow-metadata==1.17.1` |
| `egl_probe` fails to build (CMake complains about the minimum version) | Recent CMake no longer accepts the old policy version it declares | Install with `CMAKE_POLICY_VERSION_MINIMUM=3.5` |
| `gym-pusht` replaces `opencv-python-headless` with the GUI build | Its declared dependencies | Install with `--no-deps`, then add pymunk, pygame, scikit-image and shapely by hand |
| ACT and LIBERO cannot share one environment | The dm_control used by ACT requires mujoco ≥ 3.8.1, LIBERO needs 3.3.2 | Use two environments |

## Rendering

| Symptom | Cause | Fix |
|---|---|---|
| MuJoCo cannot find EGL on a headless machine | The libglvnd from conda cannot find the system NVIDIA driver | `MUJOCO_GL=egl`, and set `__EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json` |
| LIBERO images are clearly too dark | MuJoCo ≥ 3.3.3 changed rendering (LIBERO issue #88) | Pin `mujoco==3.3.2` in the LIBERO environments |

## Evaluation

| Symptom | Cause | Fix |
|---|---|---|
| The `gym_aloha` namespace is not found during evaluation | The environment is not registered in the async subprocesses | `--eval.use_async_envs=false` |
| The public ACT and Diffusion Policy checkpoints fail to load | They are in the old format | Migrate them first with LeRobot's `migrate_policy_normalization.py` |
| Diffusion Policy migration fails with `Couldn't encode 84` | Fields declared as tuple in the config are stored as list in the JSON | Wrap the migration with `scripts/eval/migrate_tuplefix.py` |
| Loading π0 or π0.5 tries to fetch the tokenizer online and is refused | The tokenizer lives in the gated repository `google/paligemma-3b-pt-224` | Request access and download the tokenizer yourself, then set `tokenizer_name` in `policy_preprocessor.json` to the local path |
| Two evaluations started together; one fails with `CUDA invalid argument` while loading the checkpoint | Two processes loading large checkpoints at the same time | Start the second one a few minutes later |

## Training

| Symptom | Cause | Fix |
|---|---|---|
| Memory explodes right after training starts and the process is killed | The wrapper script had no `if __name__ == "__main__":`, so every DataLoader worker started with spawn re-ran the whole training | Guard the entry point in every wrapper; do a real run with very few steps before queueing |
| Full fine-tuning of π0 does not fit in 24 GB | The model is too large | Train only the action expert, enable gradient checkpointing and bfloat16; at batch 16 the peak is about 15.5 GB and each step takes about 4.2 s |
