"""各分析脚本共用的统计与轨迹指标(长度单位由调用方决定,本项目用 cm)。"""
import math

import numpy as np


def ci95(pc, n):
    """二项分布正态近似的 95% 置信区间半宽(百分点)。pc 为成功率百分数。"""
    return 196 * math.sqrt(pc / 100 * (1 - pc / 100) / n)


def two_prop_z(a, b, n=100):
    """两组各 n 回合、成功 a / b 次的两比例 z 统计量(不合并方差)。"""
    p1, p2 = a / n, b / n
    se = math.sqrt(p1 * (1 - p1) / n + p2 * (1 - p2) / n)
    return (p1 - p2) / se if se else float("nan")


def dtw(a, b):
    """动态时间规整后的平均点距:消除快慢差异,只比路线。a[T1,3]、b[T2,3]。"""
    n, m = len(a), len(b)
    d = np.linalg.norm(a[:, None] - b[None], axis=2)
    D = np.full((n + 1, m + 1), np.inf)
    D[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i, j] = d[i - 1, j - 1] + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
    # 回溯路径长度做归一化
    i, j, L = n, m, 0
    while i > 0 and j > 0:
        L += 1
        k = np.argmin([D[i - 1, j - 1], D[i - 1, j], D[i, j - 1]])
        i, j = (i - 1, j - 1) if k == 0 else (i - 1, j) if k == 1 else (i, j - 1)
    return D[n, m] / L


def grasp(eef, grip):
    """抓取点:夹爪开合宽度第一次降到初始值 80% 以下时的末端位置;整回合没合拢则返回 None。"""
    w = np.abs(grip[:, 0] - grip[:, 1])
    idx = np.where(w < 0.8 * w[:5].mean())[0]
    return eef[idx[0]] if len(idx) else None


def spread(points):
    """一组点到其均值的平均距离;有效点少于 3 个时返回 nan。"""
    p = np.array([x for x in points if x is not None])
    return float(np.linalg.norm(p - p.mean(0), axis=1).mean()) if len(p) >= 3 else float("nan")
