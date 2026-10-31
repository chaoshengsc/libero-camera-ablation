# Environments

[中文](README_CN.md) · [Project overview](../README.md) · [Installation](../docs/INSTALL.md)

Configuration examples, dependency constraints, and historical package inventories. Follow the [installation guide](../docs/INSTALL.md) for the setup order. Exports support version checks; they are not a clean-machine installation verification.

| File | Purpose |
|---|---|
| [env.sh.example](env.sh.example) | Cache, temporary-directory, and environment settings under `EMB_ROOT` |
| [condarc.example](condarc.example) | Example conda directory configuration |
| [constraints-torch.txt](constraints-torch.txt) | Torch constraints for ACT / Diffusion Policy |
| [constraints-smolvla.txt](constraints-smolvla.txt) | Torch and MuJoCo constraints for SmolVLA / π0 / π0.5 |
| [constraints-ovla.txt](constraints-ovla.txt) | Independent OpenVLA dependency constraints |
| [lock/](lock/) | Package exports from three actual environments on 2026-10-01, with usage notes |

ACT / Diffusion Policy, OpenVLA, and SmolVLA / π0 / π0.5 use separate environments. Official OpenPI π0 uses its own pipeline. Constraints and historical exports do not prove the current runtime state of a machine.

After setup, choose an evaluation in the [script index](../scripts/README.md). For dependency, rendering, or decoding failures, consult [troubleshooting](../docs/TROUBLESHOOTING.md).
