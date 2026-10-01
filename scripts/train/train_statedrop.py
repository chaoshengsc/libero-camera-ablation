"""运行 lerobot-train,训练时以概率 STATE_DROP_P 按样本把 observation.state(已归一化)置零,逼策略依赖视觉。
STATE_DROP_P=0 即普通训练(对照组)。只在 policy.training 时生效,评测不受影响。不改 LeRobot 源码。"""
import os
import sys

import lerobot.scripts.lerobot_train as T
import torch
from lerobot.policies.pi0.modeling_pi0 import PI0Policy
from lerobot.utils.constants import OBS_STATE

P = float(os.environ.get("STATE_DROP_P", "0"))
_orig, _seen = PI0Policy.forward, [0, 0]

def forward(self, batch, *a, **k):
    if self.training and P > 0 and OBS_STATE in batch:
        s = batch[OBS_STATE]
        m = (torch.rand(s.shape[0], device=s.device) < P).view(-1, *[1] * (s.dim() - 1))
        batch = dict(batch); batch[OBS_STATE] = torch.where(m, torch.zeros_like(s), s)
        _seen[0] += int(m.sum()); _seen[1] += s.shape[0]
        if _seen[1] == s.shape[0]:
            print(f"[statedrop] p={P} 首个 batch 置零 {int(m.sum())}/{s.shape[0]},state 形状 {tuple(s.shape)}", flush=True)
    return _orig(self, batch, *a, **k)



if __name__ == "__main__":
    # 只在主进程里替换并启动训练;DataLoader 以 spawn 方式启动的子进程会重新导入本文件,不能在那里再起一次训练
    PI0Policy.forward = forward

    # 计时:统计相邻两次 update_policy 调用的间隔(含数据加载),每 25 步打印一次平均值;前 5 步含预热,不计入
    import time
    _up, _t = T.update_policy, {"n": 0, "last": None, "sum": 0.0, "cnt": 0}
    def update_policy(*a, **k):
        now = time.time()
        if _t["last"] is not None and _t["n"] > 5:
            _t["sum"] += now - _t["last"]; _t["cnt"] += 1
            if _t["cnt"] % 25 == 0:
                print(f"[timing] step {_t['n']} avg {_t['sum'] / _t['cnt']:.3f}s", flush=True)
        _t["last"] = now; _t["n"] += 1
        return _up(*a, **k)
    T.update_policy = update_policy
    print(f"[statedrop] STATE_DROP_P={P}", flush=True)
    sys.exit(T.main())
