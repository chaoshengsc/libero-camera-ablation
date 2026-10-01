# 环境的完整包清单

`conda env export --no-builds` 从实际跑出结果的三个环境导出(2026-10-01),用于核对版本。

- 以可编辑方式安装的源码包(lerobot、openvla、LIBERO)在清单里只有名字和版本号,需按 `docs/INSTALL_CN.md` 从对应 commit 安装。
- torch 的 `+cu128` / `+cu121` 版本需要从 PyTorch 的索引安装,不能直接 `conda env create -f`;按 `docs/INSTALL_CN.md` 的步骤装,再用这里的清单核对。
