"""Episode-local state replacement; contains no model or environment code."""
from copy import deepcopy


def clone(value):
    return value.detach().clone() if hasattr(value, "detach") else deepcopy(value)


class StateFeedback:
    def __init__(self, mode):
        if mode not in {"live", "freeze_initial"}:
            raise ValueError(f"unknown STATE_FEEDBACK={mode}")
        self.mode = mode
        self.reset()

    def reset(self):
        self.first = None

    def apply(self, state):
        if self.first is None:
            self.first = clone(state)
        return state if self.mode == "live" else clone(self.first)
