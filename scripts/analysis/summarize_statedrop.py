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


print(f"{'model':26} {'normal':>6} {'black':>6}  drop   | per task, normal / black")
print(f"{'original π0 (reference)':26} {76:>6} {56:>6}  {20:+d}")
for name, label in [("ft_p0", "fine-tuned, control p=0"), ("ft_p05", "fine-tuned, zeroing p=0.5")]:
    a, sa = rate(f"eval_{name}_normal")
    b, sb = rate(f"eval_{name}_black")
    if a is None or b is None:
        print(f"{label:26} missing results (normal {a}, black {b})")
        continue
    print(f"{label:22} {a:>6} {b:>6}  {a - b:+d}   | {sa} / {sb}")
