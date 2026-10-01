"""分析指标的单元测试:这些函数算错,README 里的结论会整个作废。"""
import math

import numpy as np
import pytest

from metrics import ci95, dtw, grasp, spread, two_prop_z


def test_ci95_matches_published_numbers():
    # README 表里的置信区间:83.2% / 500 回合 → ±3.3;98.0% → ±1.2
    assert round(ci95(83.2, 500), 1) == 3.3
    assert round(ci95(98.0, 500), 1) == 1.2
    assert ci95(0, 100) == 0 and ci95(100, 100) == 0


def test_two_prop_z_matches_published_numbers():
    # 状态置零微调:全涂黑 61 vs 40 → z≈3.0;正常 78 vs 68 → z≈1.6
    assert two_prop_z(61, 40) == pytest.approx(3.04, abs=0.01)
    assert two_prop_z(78, 68) == pytest.approx(1.60, abs=0.01)
    assert two_prop_z(50, 50) == 0
    assert two_prop_z(40, 61) == -two_prop_z(61, 40)
    assert math.isnan(two_prop_z(0, 0))


def test_dtw_ignores_speed_but_not_route():
    t = np.linspace(0, 1, 50)[:, None]
    line = np.hstack([t, np.zeros_like(t), np.zeros_like(t)])
    assert dtw(line, line) == 0
    # 同一路线、快一倍:距离应接近 0(只剩采样间隔)
    assert dtw(line, line[::2]) < 0.02
    # 平行平移 3 个单位:距离应为 3
    assert dtw(line, line + np.array([0, 3.0, 0])) == pytest.approx(3.0)
    assert dtw(line, line[::2] + np.array([0, 3.0, 0])) == pytest.approx(3.0, abs=0.02)


def test_grasp_is_first_clear_closing():
    eef = np.arange(30, dtype=float)[:, None] * np.ones((1, 3))
    grip = np.tile([0.04, -0.04], (30, 1))
    assert grasp(eef, grip) is None  # 整回合没合拢
    grip[12:] = [0.01, -0.01]
    assert grasp(eef, grip)[0] == 12
    grip[5:12] = [0.035, -0.035]  # 轻微抖动(宽度仍在 80% 以上)不算抓取
    assert grasp(eef, grip)[0] == 12


def test_spread():
    pts = [np.array([1.0, 0, 0]), np.array([-1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, -1.0, 0])]
    assert spread(pts) == pytest.approx(1.0)
    assert spread(pts + [None]) == pytest.approx(1.0)  # 没抓到的回合被忽略
    assert math.isnan(spread(pts[:2]))
