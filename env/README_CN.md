# 环境目录

[English](README.md) · [项目首页](../README_CN.md) · [安装指南](../docs/INSTALL_CN.md)

这里提供配置样例、版本约束与历史环境清单。完整安装顺序以[安装指南](../docs/INSTALL_CN.md)为准；导出清单用于核对版本，不等于已经在新机器上验证过的一键安装。

| 文件 | 用途 |
|---|---|
| [env.sh.example](env.sh.example) | `EMB_ROOT` 下的缓存、临时目录与环境设置样例 |
| [condarc.example](condarc.example) | conda 的目录配置样例 |
| [constraints-torch.txt](constraints-torch.txt) | ACT / Diffusion Policy 使用的 torch 版本约束 |
| [constraints-smolvla.txt](constraints-smolvla.txt) | SmolVLA / π0 / π0.5 的 torch 与 MuJoCo 约束 |
| [constraints-ovla.txt](constraints-ovla.txt) | OpenVLA 的独立依赖约束 |
| [lock/](lock/) | 2026-10-01 从三个实际环境导出的包清单及使用说明 |

ACT / Diffusion Policy、OpenVLA、SmolVLA / π0 / π0.5 使用不同环境；官方OpenPI π0另用独立JAX环境，[安装指南](../docs/OPENPI_CN.md)记录固定源码/锁文件指纹、Python/uv版本与已核对包元数据。上面三份历史环境导出不包含OpenPI，不将约束文件或旧清单当成当前机器的运行证明。

装好后到[脚本索引](../scripts/README_CN.md)选择评测入口；遇到依赖、渲染或解码问题，查[排错文档](../docs/TROUBLESHOOTING_CN.md)。

换设备继续实验的材料与验收顺序见[迁移准备](../docs/CONTINUE_CN.md)。约束现已固定`hf-libero==0.1.4`，与历史清单和素材准备检查一致；这不等于新设备已验收。
