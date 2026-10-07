# 踩坑与解决办法

[English](TROUBLESHOOTING.md) | 中文

按“现象 → 原因 → 解决”整理，都是这次复现里实际遇到的。

## 安装

| 现象 | 原因 | 解决 |
|---|---|---|
| torch 装好后 `cuda.is_available()` 为 False 或报 CUDA 版本错 | PyPI 默认的 torch 是 CUDA 13 版，驱动 570 不支持 | 从 `https://download.pytorch.org/whl/cu128` 装，并用约束文件锁住 torch |
| 视频解码报错（torchcodec） | torchcodec 0.11 不支持 ffmpeg 9 | conda 里固定 `ffmpeg=7.1.1` |
| `flash-attn` 安装要求 `CUDA_HOME` | 源码编译需要完整 CUDA 工具链 | 直接装官方 Release 里的预编译 wheel |
| LIBERO `pip install -e .` 后 `import libero` 失败 | 新版 setuptools 的可编辑安装方式与它的包结构不兼容 | `pip install -e . --config-settings editable_mode=compat` |
| OpenVLA 环境 `pip check` 报 protobuf 冲突 | tensorflow-metadata 与 protobuf 版本互相限制 | `protobuf==4.21.12` + `tensorflow-metadata==1.17.1` |
| `egl_probe` 编译失败（CMake 报最低版本） | 新版 CMake 不再接受它声明的旧策略版本 | 安装时加 `CMAKE_POLICY_VERSION_MINIMUM=3.5` |
| `gym-pusht` 把 `opencv-python-headless` 换成了带界面的版本 | 它的依赖声明 | 用 `--no-deps` 装，再手动补 pymunk、pygame、scikit-image、shapely |
| ACT 与 LIBERO 装不进同一个环境 | ACT 用的 dm_control 要求 mujoco ≥ 3.8.1，LIBERO 需要 3.3.2 | 分成两个环境 |

## 渲染

| 现象 | 原因 | 解决 |
|---|---|---|
| 无显示器的机器上 MuJoCo 找不到 EGL | conda 里的 libglvnd 找不到系统的 NVIDIA 驱动 | `MUJOCO_GL=egl`，并设 `__EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json` |
| LIBERO 画面明显偏暗 | MuJoCo ≥ 3.3.3 改了渲染（LIBERO issue #88） | LIBERO 相关环境固定 `mujoco==3.3.2` |

## 评测

| 现象 | 原因 | 解决 |
|---|---|---|
| `gym_aloha` 命名空间在评测时找不到 | 异步子进程里没有注册环境 | `--eval.use_async_envs=false` |
| ACT、Diffusion Policy 的公开权重加载失败 | 权重是旧格式 | 先用 LeRobot 的 `migrate_policy_normalization.py` 迁移 |
| Diffusion Policy 迁移报 `Couldn't encode 84` | 配置里声明为 tuple 的字段，JSON 里存的是 list | 用 `scripts/eval/migrate_tuplefix.py` 包一层 |
| π0、π0.5 加载时要联网取分词器并被拒绝 | 分词器在受限仓库 `google/paligemma-3b-pt-224` | 自己申请授权下载分词器，把 `policy_preprocessor.json` 的 `tokenizer_name` 改成本地路径 |
| 两个评测同时启动，其中一个加载权重时报 `CUDA invalid argument` | 两个进程同时加载大权重 | 第二个进程错开几分钟启动 |

## 训练

| 现象 | 原因 | 解决 |
|---|---|---|
| 训练一启动内存暴涨、进程被杀 | 包装脚本没有 `if __name__ == "__main__":`，DataLoader 以 spawn 方式启动的每个子进程都重新执行了一遍训练 | 所有包装脚本加入口保护；排队前先用很少的步数实跑一次 |
| π0 全量微调显存不够（24 GB） | 模型太大 | 只训动作专家、开梯度检查点、bfloat16；batch 16 时峰值约 15.5 GB，每步约 4.2 秒 |
