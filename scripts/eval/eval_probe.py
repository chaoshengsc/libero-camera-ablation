"""运行 lerobot-eval,并(1)按 BLACKOUT 涂黑送进策略的相机画面,(2)逐步记录末端执行器轨迹。不改 LeRobot 源码。
BLACKOUT=none(默认)| all | agent(只涂主视角)| wrist(只涂腕部相机)
         | noise(两路加高斯噪声,标准差 NOISE_STD,默认 0.1,像素范围 [0,1])
         | freeze(整个回合都给第 1 帧画面:真实、分布内,但不再更新)
         | freeze_wrist / freeze_agent(只冻结这一路:整个回合都给它第 1 帧的真实画面,另一路正常更新)
         | drop_wrist / drop_agent / drop_all(去掉这一路 / 两路相机:在 π0/π0.5 内部把该相机槽填 -1、注意力掩码设为 0,
           与训练时空相机槽的处理相同;涂黑则掩码仍为 1。不能直接从输入里删键:LeRobot 会把在场的图像排在前面、
           缺失的补在后面,删掉主视角时腕部画面会被挪进主视角的槽位)
π0 的权重若带 absolute_actions_processor(OpenPI 官方 pi0_libero 的 extra_delta_transform,见 adapt_openpi_pi0.py),
加回增量时改用动作块开始那一步的状态(与 OpenPI 一致),并打印归一化后的状态、还原前后的动作作为证据。
DELTA_REF=chunk(默认)| step(诊断用:保留 LeRobot 原本的做法,用当前这一步的状态,只打印证据)
POLICY_SERVER=<端口>:不用 LeRobot 的策略,改向本机 OpenPI 原版服务端(scripts/openpi/serve_pi0_libero.py)要动作块,
           每块执行前 --policy.n_action_steps 步;需要 OPENPI_AUTHKEY。环境、初始状态、BLACKOUT 处理都不变,
           drop_* 由服务端把对应槽位的 image_mask 置 0。--policy.path 仍要给一个 π0 权重目录,只用来解析配置,不加载权重。
TRAJ_OUT=<npz 路径>:每回合一条轨迹,字段 eef[T,3]、grip[T,2]、act[T,7](实际送进环境 step 的动作,开环回放用);
         按 rollout 调用顺序(batch_size=1 时即 任务0回合0..9, 任务1…)。"""
import atexit
import hashlib
import os
import sys

import lerobot.scripts.lerobot_eval as E
import numpy as np
import torch

MODE = os.environ.get("BLACKOUT", "none")
assert MODE in {"none", "all", "agent", "wrist", "noise", "freeze", "drop_wrist", "drop_agent", "drop_all", "freeze_wrist", "freeze_agent"}, f"unknown BLACKOUT={MODE}"
TRAJ_OUT = os.environ.get("TRAJ_OUT")
DELTA_REF = os.environ.get("DELTA_REF", "chunk")
POLICY_SERVER = os.environ.get("POLICY_SERVER")
SLOT = {"observation.images.image": "base_0_rgb", "observation.images.image2": "left_wrist_0_rgb"}  # OpenPI LiberoInputs 的槽位
assert DELTA_REF in {"chunk", "step"}, f"unknown DELTA_REF={DELTA_REF}"
NOISE_STD = float(os.environ.get("NOISE_STD", "0.1"))
_first = {}
_step = [0]
_dropped = []  # drop_* 模式下要屏蔽的相机键
_masked = []  # π0/π0.5 的包装确实按槽位屏蔽过一次后置位;其他策略没有这层包装
_chunk = {}  # 增量动作还原的参考状态:本段动作块开始那一步的原始状态;另记动作越界次数等证据
_pre, _roll, _shown = E.preprocess_observation, E.rollout, False
episodes = []  # 每项:{"eef": [...], "grip": [...], "act": [...]}


def _hit(k):
    if MODE in ("all", "drop_all"):
        return True
    wrist = any(s in k for s in ("eye_in_hand", "wrist")) or k.endswith("image2")
    return wrist if MODE in ("wrist", "drop_wrist", "freeze_wrist") else not wrist


def pre(obs):
    global _shown
    st = obs.get("robot_state") if isinstance(obs, dict) else None
    if st is not None and episodes:
        assert len(st["eef"]["pos"]) == 1, "trajectory logging requires --eval.batch_size=1"
        episodes[-1]["eef"].append(np.asarray(st["eef"]["pos"])[0].copy())
        episodes[-1]["grip"].append(np.asarray(st["gripper"]["qpos"])[0].copy())
    out = _pre(obs)
    keys = [k for k in out if k.startswith("observation.image")]
    _step[0] += 1
    if episodes and "h0" not in episodes[-1]:  # 本回合第 1 帧主视角的哈希:用来核对两次运行的同一回合是否同一初始状态
        episodes[-1]["h0"] = hashlib.md5(out[keys[0]].cpu().numpy().round(3).tobytes()).hexdigest()[:12]
    if MODE == "noise":
        for k in keys:
            out[k] = (out[k] + NOISE_STD * torch.randn_like(out[k])).clamp(0, 1)
    elif MODE in ("freeze", "freeze_wrist", "freeze_agent"):
        hit = keys if MODE == "freeze" else [k for k in keys if _hit(k)]
        assert hit and (MODE == "freeze" or len(hit) == 1), f"{MODE}: expected one camera to freeze, got {hit}"
        if not _first:  # 本回合第 1 步:记下画面(roll() 在每回合开始时清空)
            _first.update({k: out[k].clone() for k in keys})
        for k in hit:
            out[k] = _first[k].clone()
        if len(episodes) == 1 and _step[0] == 20:  # 第 1 回合第 20 步(替换之后):冻结的那路应为 0,其余应大于 0
            print("[probe] freeze check at step 20, max |sent - frame1|:",
                  {k: round(float((out[k] - _first[k]).abs().max()), 4) for k in keys}, "(frozen:", hit, ")", flush=True)
    elif MODE.startswith("drop_"):
        hit = [k for k in keys if _hit(k)]
        assert len(hit) == (2 if MODE == "drop_all" else 1), f"{MODE}: unexpected cameras to drop: {hit}"
        # 第 1 步之后策略至少推理过一次;没屏蔽过说明策略不是 π0/π0.5,drop 会退化成涂黑
        assert _step[0] == 1 or _masked, f"{MODE} only works with π0/π0.5: the camera was not masked in its slot"
        _dropped[:] = hit
        for k in hit:
            out[k] = torch.zeros_like(out[k])  # 真正的屏蔽在 _log_masks 的包装里按槽位完成
    elif MODE != "none":
        for k in keys:
            if _hit(k):
                out[k] = torch.zeros_like(out[k])
    if not _shown:
        print(f"[probe] BLACKOUT={MODE} NOISE_STD={NOISE_STD}", {k: (tuple(v.shape), float(v.float().abs().max())) for k, v in out.items()
                                          if k.startswith("observation.image")}, "| robot_state:", st is not None, flush=True)
        _shown = True
    return out


def _log_masks():
    """π0/π0.5:drop_* 模式下在原槽位屏蔽该相机(填 -1、掩码 0);第一次进入策略时打印每个槽位的掩码与像素范围。"""
    from lerobot.policies.pi0.modeling_pi0 import PI0Policy
    from lerobot.policies.pi05.modeling_pi05 import PI05Policy
    _masks_shown = []
    for cls in (PI0Policy, PI05Policy):
        def wrapped(self, batch, _orig=cls._preprocess_images, _masks_shown=_masks_shown):
            images, masks = _orig(self, batch)
            slots = list(self.config.image_features)
            assert len(images) == len(slots) and all(k in batch for k in slots[:len(slots) - self.config.empty_cameras]), \
                "slot order assumption broken: a real camera is missing from the batch"
            for k in _dropped:
                i = slots.index(k)
                images[i] = torch.ones_like(images[i]) * -1
                masks[i] = torch.zeros_like(masks[i])
                _masked[:] = [True]
            if not _masks_shown:
                print("[probe] slots/mask/pixel range:", [(k.split(".")[-1], bool(m[0]), round(float(i.min()), 2), round(float(i.max()), 2))
                                                          for k, m, i in zip(slots, masks, images, strict=True)], flush=True)
                _masks_shown.append(True)
            return images, masks
        cls._preprocess_images = wrapped


def _delta_ref():
    """OpenPI 的 AbsoluteActions 对整段动作块加同一个状态(推理那一刻的原始状态,policy.py 把输入的 state 原样放进输出);
    LeRobot 的 lerobot_eval 每一步都跑一遍前后处理,AbsoluteActionsProcessorStep 读到的是当前这一步缓存的状态,
    动作块第 2 步起就加错。这里让它改读动作块开始那一步的状态。权重不带 absolute_actions_processor 时不起作用。"""
    from lerobot.policies.pi0.modeling_pi0 import PI0Policy
    from lerobot.processor.relative_action_processor import AbsoluteActionsProcessorStep, RelativeActionsProcessorStep

    def select(self, batch, _orig=PI0Policy.select_action):
        if len(self._action_queue) == 0:  # 这一步要推理新的动作块
            _chunk["new"] = True
            st = batch.get("observation.state")
            if st is not None:
                _chunk["state_absmax"] = max(_chunk.get("state_absmax", 0.0), float(st.abs().max()))
        return _orig(self, batch)

    def cached(self):
        if _chunk.pop("new", False) or "ref" not in _chunk:
            _chunk["ref"] = self._last_state.clone()
        return _chunk["ref"]

    def absolute(self, transition, _orig=AbsoluteActionsProcessorStep.__call__):
        from lerobot.lerobot_types import TransitionKey
        before = transition.get(TransitionKey.ACTION)
        out = _orig(self, transition)
        if self.relative_step is not None:  # 步骤未启用时(不加增量)也记录最终动作的越界情况
            a = out[TransitionKey.ACTION]
            _chunk["n"] = _chunk.get("n", 0) + 1
            _chunk["over"] = _chunk.get("over", 0) + int((a[..., :6].abs() > 1).any())
            if len(episodes) == 1 and _step[0] <= 7:  # 第 1 回合前 7 步:第 6 步起换新动作块,参考状态应随之更新
                r = lambda t: [round(float(x), 3) for x in t.reshape(-1)[:7]]  # noqa: E731
                ref = _chunk["ref"] if DELTA_REF == "chunk" and self.enabled else self.relative_step._last_state
                print(f"[probe] delta step {_step[0]}: before {r(before)} ref_state {r(ref)} "
                      f"current_state {r(self.relative_step._last_state)} after {r(a)}", flush=True)
        return out

    PI0Policy.select_action = select
    if DELTA_REF == "chunk":
        RelativeActionsProcessorStep.get_cached_state = cached
    AbsoluteActionsProcessorStep.__call__ = absolute


def _remote():
    """把 lerobot_eval 里的策略换成 OpenPI 服务端的代理;前后处理换成恒等(归一化、增量还原都在服务端按 OpenPI 原样做)。"""
    from multiprocessing.connection import Client

    from lerobot.policies import PreTrainedPolicy
    from lerobot.policies.pi0.configuration_pi0 import PI0Config

    conn = Client(("127.0.0.1", int(POLICY_SERVER)), authkey=os.environ["OPENPI_AUTHKEY"].encode())

    def pack(a):
        a = np.ascontiguousarray(a)
        return a.tobytes(), a.shape, a.dtype.str

    def u8(t):  # (1, 3, H, W) 的 [0, 1] 浮点图 → (H, W, 3) uint8;preprocess_observation 是 uint8 / 255 得来的,这里原样还原
        return t[0].permute(1, 2, 0).mul(255).round().clamp(0, 255).to(torch.uint8).cpu().numpy()

    class OpenPIRemote(PreTrainedPolicy):
        config_class = PI0Config
        name = "openpi_remote"

        def __init__(self, config):
            super().__init__(config)
            self.queue = []

        def reset(self):
            self.queue = []

        def get_optim_params(self):
            return {}

        def forward(self, batch):
            raise NotImplementedError

        def predict_action_chunk(self, batch, **kwargs):
            raise NotImplementedError

        def select_action(self, batch, **kwargs):
            if not self.queue:
                assert len(batch["task"]) == 1, "POLICY_SERVER requires --eval.batch_size=1"
                img, wrist = u8(batch["observation.images.image"]), u8(batch["observation.images.image2"])
                for nm, x in (("agent", img), ("wrist", wrist)):  # 证据:每回合送出的每路画面有几种(冻结的那路应只有 1 种)
                    episodes[-1].setdefault(nm + "_sent", set()).add(hashlib.md5(x.tobytes()).hexdigest())
                req = {"image": pack(img), "wrist_image": pack(wrist),
                       "state": pack(batch["observation.state"][0].double().cpu().numpy()), "prompt": batch["task"][0],
                       "drop": [SLOT[k] for k in _dropped]}
                conn.send(req)
                rep = conn.recv()
                b, shape, dtype = rep["actions"]
                chunk = np.frombuffer(b, dtype=dtype).reshape(shape)
                if _dropped:
                    assert not any(rep["masks"][SLOT[k]] for k in _dropped), rep["masks"]
                    _masked[:] = [True]
                if "shown" not in _chunk:
                    _chunk["shown"] = True
                    print(f"[probe] remote: masks {rep['masks']} image {rep['image_shape']} chunk {chunk.shape} infer_ms {rep['infer_ms']:.0f}"
                          f" state {[round(float(x), 3) for x in batch['observation.state'][0]]}"
                          f" first actions {[[round(float(x), 3) for x in a] for a in chunk[:2]]}", flush=True)
                self.queue = [torch.from_numpy(chunk[i].copy()).unsqueeze(0) for i in range(self.config.n_action_steps)]
            a = self.queue.pop(0)
            _chunk["n"] = _chunk.get("n", 0) + 1
            _chunk["over"] = _chunk.get("over", 0) + int((a[..., :6].abs() > 1).any())
            return a

    E.make_policy = lambda cfg, env_cfg=None, rename_map=None, **k: OpenPIRemote(cfg)
    E.make_pre_post_processors = lambda *a, **k: (lambda x: x, lambda x: x)


def roll(*a, **k):
    episodes.append({"eef": [], "grip": [], "act": []})
    _chunk.pop("ref", None)
    _first.clear()
    _step[0] = 0
    env = k["env"] if "env" in k else a[0]
    step = env.step

    def logged(action):  # 记录实际送进环境的动作(batch_size=1),供 scripts/analysis/replay_open_loop.py 开环回放
        episodes[-1]["act"].append(np.asarray(action)[0].copy())
        return step(action)

    env.step = logged
    try:
        return _roll(*a, **k)
    finally:
        del env.step  # 去掉实例上的包装,恢复类方法


def _save():
    if "n" in _chunk:
        print(f"[probe] DELTA_REF={DELTA_REF}, actions logged on {_chunk['n']} steps; steps with |action[:6]| > 1: {_chunk['over']}; "
              f"max |normalized state| at inference: {_chunk.get('state_absmax', float('nan')):.3f}", flush=True)
    if POLICY_SERVER and episodes:
        for nm in ("agent", "wrist"):
            n = [len(e.get(nm + "_sent", ())) for e in episodes]
            print(f"[probe] distinct {nm} images sent per episode: min {min(n)}, max {max(n)}", flush=True)
    if TRAJ_OUT and episodes:
        np.savez_compressed(TRAJ_OUT, n=len(episodes),
                            **{f"eef_{i}": np.array(e["eef"]) for i, e in enumerate(episodes)},
                            **{f"grip_{i}": np.array(e["grip"]) for i, e in enumerate(episodes)},
                            **{f"act_{i}": np.array(e["act"]) for i, e in enumerate(episodes)},
                            h0=np.array([e.get("h0", "") for e in episodes]))
        print(f"[probe] saved {len(episodes)} episodes -> {TRAJ_OUT}", flush=True)


# 入口保护:多进程以 spawn 方式启动时子进程会重新导入本文件,没有保护会重复执行主流程
if __name__ == "__main__":
    atexit.register(_save)
    E.preprocess_observation, E.rollout = pre, roll
    _log_masks()
    _delta_ref()
    if POLICY_SERVER:
        _remote()
    sys.exit(E.main())
