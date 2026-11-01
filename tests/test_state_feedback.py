"""Cache semantics without heavyweight model dependencies."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("state_feedback", Path(__file__).parents[1] / "scripts/eval/state_feedback.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_live_and_frozen_isolation_and_reset():
    for mode in ("live", "freeze_initial"):
        cache = MODULE.StateFeedback(mode)
        first, second = [[1, 2, 0]], [[3, 4, 0]]
        sent = cache.apply(first)
        if mode == "freeze_initial":
            sent[0][0] = 99
        assert first == [[1, 2, 0]]
        assert cache.apply(second) == (second if mode == "live" else first)
        assert second == [[3, 4, 0]]
        cache.reset()
        assert cache.apply(second) == second


def test_unknown_mode():
    with pytest.raises(ValueError):
        MODULE.StateFeedback("typo")


def test_real_tensor_preserves_input_padding_and_rng():
    torch = pytest.importorskip("torch")
    first = torch.arange(32, dtype=torch.float32).reshape(1, 32)
    first[:, 8:] = 0
    second = first.clone()
    second[:, :8] += 2
    untouched = second.clone()
    for mode in ("live", "freeze_initial"):
        cache = MODULE.StateFeedback(mode)
        rng = torch.random.get_rng_state().clone()
        cache.apply(first)
        sent = cache.apply(second)
        assert torch.equal(torch.random.get_rng_state(), rng)
        assert torch.equal(second, untouched)
        assert torch.equal(sent, first if mode == "freeze_initial" else second)
        assert sent.dtype == second.dtype and sent.device == second.device
        assert torch.equal(sent[:, 8:], second[:, 8:])
        cache.reset()
        assert torch.equal(cache.apply(second), second)
