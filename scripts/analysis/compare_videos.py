"""实验 b:π0 是否"背轨迹"。逐帧比较同任务、同回合编号(同初始状态)的录像。
D_bn  = π0 全涂黑 vs π0 正常      —— 小:说明看不看画面动作都差不多
D_ctl = π0.5 正常 vs π0 正常(对照)—— 两个都看得见的不同策略,作为"真正不同的轨迹"的尺度
指标:缩小到 90×90 灰度后逐帧平均绝对差(0–255),按时间步对齐,只比两段共同长度内的帧。
自检:第 0 帧应几乎相同(同初始场景),否则回合没对齐。"""
import json
import os

import av
import numpy as np

EMB = os.environ.get("EMB_ROOT", "/path/to/emb")

E = EMB + "/logs/eval"


def frames(path):
    out = []
    with av.open(path) as c:
        for f in c.decode(video=0):
            g = f.to_ndarray(format="gray")
            h, w = g.shape
            out.append(g[: h - h % 90, : w - w % 90].reshape(90, (h - h % 90) // 90, 90, (w - w % 90) // 90).mean((1, 3)))
    return np.stack(out)


def diff(a, b):
    n = min(len(a), len(b))
    d = np.abs(a[:n] - b[:n]).mean((1, 2))
    return {"first": float(d[0]), "mean": float(d.mean()), "last": float(d[-1]), "n": n, "len": (len(a), len(b))}


def succ(run):
    import glob
    per = json.load(open(glob.glob(f"{E}/{run}/out/**/eval_info.json", recursive=True)[0]))["per_task"]
    return {t["task_id"]: t["metrics"]["successes"] for t in per}


s_black, s_norm = succ("pi0_black_all"), succ("pi0_spatial_500")
rows = []
for task in range(10):
    for ep in range(10):
        v = lambda r: f"{E}/{r}/out/videos/libero_spatial_{task}/eval_episode_{ep}.mp4"  # noqa: B023
        pn, pb, p5 = frames(v("pi0_spatial_500")), frames(v("pi0_black_all")), frames(v("pi05_spatial_500"))
        rows.append({"task": task, "ep": ep, "bn": diff(pb, pn), "ctl": diff(p5, pn),
                     "black_ok": bool(s_black[task][ep]), "norm_ok": bool(s_norm[task][ep])})
json.dump(rows, open(f"{E}/traj_compare.json", "w"))

f = lambda k, key, sel=lambda r: True: np.mean([r[k][key] for r in rows if sel(r)])
print(f"自检 第0帧差异:  π0黑vsπ0正常 {f('bn','first'):.2f}   π0.5vsπ0 {f('ctl','first'):.2f}  (应接近 0)")
print(f"全程平均差异:    π0黑vsπ0正常 {f('bn','mean'):.2f}   π0.5vsπ0(对照) {f('ctl','mean'):.2f}")
print(f"  仅看涂黑仍成功的回合: {f('bn','mean', lambda r: r['black_ok']):.2f}  (n={sum(r['black_ok'] for r in rows)})")
print(f"  仅看涂黑失败的回合:   {f('bn','mean', lambda r: not r['black_ok']):.2f}  (n={sum(not r['black_ok'] for r in rows)})")
print("各任务 全程平均差异 [π0黑vsπ0正常 / 对照] 与涂黑成功数:")
for t in range(10):
    sel = lambda r, t=t: r["task"] == t
    print(f"  task {t}: {f('bn','mean',sel):5.2f} / {f('ctl','mean',sel):5.2f}   黑成功 {sum(r['black_ok'] for r in rows if r['task']==t)}/10")
