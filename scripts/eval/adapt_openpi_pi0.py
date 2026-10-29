"""把 lerobot/pi0_libero_base(OpenPI 官方 pi0_libero 的 PyTorch 转换版)整理成能按 OpenPI 原样推理的本地副本。不改原下载目录。
用法: python adapt_openpi_pi0.py <原权重目录> <输出目录> <分词器目录> [embedded]
  embedded(诊断用):改用 model.safetensors 里夹带的旧格式归一化缓冲区,且不加增量还原(第 1、2 条换成这一种)。
  这些缓冲区的状态统计与 OpenPI 完全一致,动作统计却像未减状态的原始动作,两者只能有一个与训练时一致。
原权重目录里要有 OpenPI 官方的 openpi_norm_stats.json(gs://openpi-assets/checkpoints/pi0_libero/assets/physical-intelligence/libero/norm_stats.json)。
做四件事(依据 OpenPI src/openpi/training/config.py 的 pi0_libero 与 LeRobotLiberoDataConfig):
  1. 注入归一化统计量:转换版的 normalizer 步骤 "features": {},LeRobot 找不到统计量时会静默跳过归一化。
     π0 用均值/标准差(use_quantile_norm 只对非 PI0 打开);OpenPI 的统计量补零到 32 维,状态取前 8 维、动作取前 7 维。
  2. extra_delta_transform=True:训练时动作前 6 维减去原始状态前 6 维(夹爪除外,make_bool_mask(6, -1))。
     这里在归一化之前加 relative_actions_processor(只缓存原始状态),反归一化之后加 absolute_actions_processor(加回状态)。
     LeRobot 逐步后处理时会用当前这一步的状态,OpenPI 对整段动作块用推理那一刻的状态;这一差别由 eval_probe.py 修正。
  3. 分词器指向本地副本(google/paligemma-3b-pt-224 是受限仓库,工作站离线)。
  4. dtype 改为 bfloat16:转换版写的是 float32;OpenPI src/openpi/models/pi0_config.py 默认 bfloat16,以前 LeRobot π0 的运行也是 bfloat16。
模型权重用符号链接,不复制。"""
import json
import shutil
import sys
from pathlib import Path

import torch
from safetensors import safe_open
from safetensors.torch import save_file

SRC, OUT, TOK = (Path(a) for a in sys.argv[1:4])
EMBEDDED = sys.argv[4:] == ["embedded"]
assert sys.argv[4:] in ([], ["embedded"]), sys.argv[4:]
ACTION_NAMES = ["x", "y", "z", "roll", "pitch", "yaw", "gripper"]  # 只用来让 exclude_joints 排除第 7 维(夹爪)

ns = json.loads((SRC / "openpi_norm_stats.json").read_text())["norm_stats"]
stats = {}
for key, src_key, dim in (("observation.state", "state", 8), ("action", "actions", 7)):
    for s in ("mean", "std"):
        v = ns[src_key][s]
        assert len(v) == 32 and not any(v[dim:]), f"{src_key}.{s}: expected 32 dims zero-padded after {dim}"
        stats[f"{key}.{s}"] = torch.tensor(v[:dim], dtype=torch.float32)
if EMBEDDED:
    with safe_open(SRC / "model.safetensors", "pt") as f:
        for key, buf in (("observation.state", "normalize_inputs.buffer_observation_state"), ("action", "normalize_targets.buffer_action")):
            for s in ("mean", "std"):
                stats[f"{key}.{s}"] = f.get_tensor(f"{buf}.{s}").float().reshape(-1)

pre = json.loads((SRC / "policy_preprocessor.json").read_text())
post = json.loads((SRC / "policy_postprocessor.json").read_text())
names = [s["registry_name"] for s in pre["steps"]]
assert names == ["rename_observations_processor", "to_batch_processor", "pi0_new_line_processor", "tokenizer_processor",
                 "device_processor", "normalizer_processor"], names
assert [s["registry_name"] for s in post["steps"]] == ["unnormalizer_processor", "device_processor"]
assert pre["steps"][5]["config"]["features"] == {} and pre["steps"][5]["config"]["norm_map"]["STATE"] == "MEAN_STD"

features = {"observation.state": {"type": "STATE", "shape": [8]}, "action": {"type": "ACTION", "shape": [7]}}
pre["steps"][3]["config"]["tokenizer_name"] = str(TOK)
pre["steps"][5]["config"]["features"] = features
pre["steps"].insert(5, {"registry_name": "relative_actions_processor",
                        "config": {"enabled": not EMBEDDED, "exclude_joints": ["gripper"], "action_names": ACTION_NAMES}})
pre["steps"][6]["state_file"] = "policy_preprocessor_step_6_normalizer_processor.safetensors"
post["steps"][0]["config"]["features"] = {"action": features["action"]}
post["steps"][0]["state_file"] = "policy_postprocessor_step_0_unnormalizer_processor.safetensors"
post["steps"].insert(1, {"registry_name": "absolute_actions_processor", "config": {"enabled": not EMBEDDED}})

OUT.mkdir(parents=True, exist_ok=False)
(OUT / "model.safetensors").symlink_to(SRC / "model.safetensors")
cfg = json.loads((SRC / "config.json").read_text())
assert cfg["type"] == "pi0" and cfg["dtype"] == "float32" and cfg["empty_cameras"] == 1, cfg
cfg["dtype"] = "bfloat16"
(OUT / "config.json").write_text(json.dumps(cfg, indent=4))
for f in ("README.md", "openpi_norm_stats.json"):
    shutil.copy2(SRC / f, OUT / f)
(OUT / "policy_preprocessor.json").write_text(json.dumps(pre, indent=2))
(OUT / "policy_postprocessor.json").write_text(json.dumps(post, indent=2))
save_file({k: v for k, v in stats.items()}, OUT / pre["steps"][6]["state_file"])
save_file({k: v for k, v in stats.items() if k.startswith("action.")}, OUT / post["steps"][0]["state_file"])
print("wrote", OUT, {k: [round(x, 4) for x in v.tolist()] for k, v in stats.items()})
