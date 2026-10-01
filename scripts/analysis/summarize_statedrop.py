"""状态置零微调汇总:两组继续微调(对照 p=0 / 状态置零 p=0.5)的正常与全涂黑成功率,对比原始 π0(同协议 76 / 56)。"""
import glob
import json
import os

EMB = os.environ.get("EMB_ROOT", "/path/to/emb")

E = EMB + "/logs/eval"


def rate(run):
    f = glob.glob(f"{E}/{run}/out/**/eval_info.json", recursive=True)
    if not f:
        return None, None
    per = json.load(open(f[0]))["per_task"]
    s = [sum(t["metrics"]["successes"]) for t in per]
    return sum(s), s


print(f"{'模型':22} {'正常':>6} {'全涂黑':>6}  下降   | 正常各任务 / 涂黑各任务")
print(f"{'原始 π0(参照)':22} {76:>6} {56:>6}  {20:+d}")
for name, label in [("ft_p0", "继续微调·对照 p=0"), ("ft_p05", "继续微调·状态置零 p=0.5")]:
    a, sa = rate(f"eval_{name}_normal")
    b, sb = rate(f"eval_{name}_black")
    if a is None or b is None:
        print(f"{label:22} 结果缺失(正常 {a},涂黑 {b})")
        continue
    print(f"{label:22} {a:>6} {b:>6}  {a - b:+d}   | {sa} / {sb}")
