"""P1 state-input ablation. Use the reviewed state-feedback runner, not directly."""
import atexit
import inspect
import json
import os
import sys
from pathlib import Path

import eval_probe as P
import numpy as np
import torch
from state_feedback import StateFeedback

MODE = os.environ["STATE_FEEDBACK"]
REPEAT = int(os.environ["STATE_REPEAT"])
OUT = Path(os.environ["STATE_EVIDENCE"])
assert REPEAT in range(3) and P.MODE in {"none", "all"} and not P.POLICY_SERVER
cache = StateFeedback(MODE)
rows = []
current = None


def array(x):
    return x.detach().float().cpu().numpy().copy()


def install():
    from lerobot.policies.pi0.modeling_pi0 import PI0Policy
    original_state, original_reset = PI0Policy.prepare_state, PI0Policy.reset
    original_select, original_images = PI0Policy.select_action, PI0Policy._preprocess_images
    original_roll = P.roll
    signature = inspect.signature(P._roll)

    def reset(self):
        cache.reset()
        return original_reset(self)

    def state(self, batch):
        incoming = batch["observation.state"].clone()
        prepared = original_state(self, batch)
        sent = cache.apply(prepared)
        assert torch.equal(incoming, batch["observation.state"])
        assert sent.shape == prepared.shape == (1, 32) and torch.isfinite(sent).all()
        assert sent.dtype == prepared.dtype and sent.device == prepared.device
        assert torch.equal(sent[:, 8:], prepared[:, 8:])
        if MODE == "live":
            assert torch.equal(sent, prepared)
        else:
            assert torch.equal(sent, cache.first)
        current["normalized"].append(array(prepared))
        current["sent"].append(array(sent))
        current["inference_steps"].append(P._step[0])
        return sent

    def images(self, batch):
        values, masks = original_images(self, batch)
        slots = list(self.config.image_features)
        assert slots[:2] == ["observation.images.image", "observation.images.image2"]
        assert [bool(m[0]) for m in masks] == [True, True, False]
        if P.MODE == "all":
            assert all(torch.count_nonzero(batch[k]) == 0 for k in slots[:2])
        current["masks"] = [bool(m[0]) for m in masks]
        current["image_checks"] += 1
        return values, masks

    def select(self, batch):
        assert type(self) is PI0Policy and self.config.n_action_steps == 5
        assert batch["observation.state"].shape == (1, 8)
        if not current["seeded"]:
            torch.manual_seed(current["noise_seed"])
            torch.cuda.manual_seed_all(current["noise_seed"])
            current["seeded"] = True
        return original_select(self, batch)

    def roll(*args, **kwargs):
        global current
        bound = signature.bind(*args, **kwargs).arguments
        env = bound["env"]
        assert env.num_envs == 1
        task = int(env.call("task_id")[0])
        initial = int(env.call("init_state_id")[0])
        seeds = bound.get("seeds")
        assert 0 <= task < 10 and 0 <= initial < 10 and list(seeds) == [1000 + initial]
        current = {"task": task, "initial": initial, "repeat": REPEAT,
                   "noise_seed": 20261031 + 1000 * REPEAT + 50 * task + initial,
                   "seeded": False, "normalized": [], "sent": [], "raw_steps": [], "inference_steps": [], "image_checks": 0}
        raw_processor = bound["env_preprocessor"]

        def raw(observation):
            out = raw_processor(observation)
            current["raw_steps"].append(array(out["observation.state"]))
            return out

        bound["env_preprocessor"] = raw
        result = original_roll(**bound)
        assert current["seeded"] and current["image_checks"] == len(current["sent"]) > 0
        row = {k: v for k, v in current.items() if k not in {"normalized", "sent", "raw_steps"}}
        row["first_frame_hash"] = P.episodes[-1]["h0"]
        row["eef0"] = P.episodes[-1]["eef"][0].tolist()
        row["state_changes"] = any(not np.array_equal(x, current["normalized"][0]) for x in current["normalized"])
        row["sent_changes"] = any(not np.array_equal(x, current["sent"][0]) for x in current["sent"])
        row["state_file"] = f"state_{task}_{initial}.npz"
        np.savez_compressed(OUT.parent / row["state_file"], normalized=np.array(current["normalized"]),
                            sent=np.array(current["sent"]), raw=np.array(current["raw_steps"]), inference_steps=current["inference_steps"])
        rows.append(row)
        OUT.write_text(json.dumps({"mode": MODE, "blackout": P.MODE, "episodes": rows}, indent=2))
        print(f"[statefb] task={task} init={initial} blocks={row['image_checks']} state_changes={row['state_changes']} sent_changes={row['sent_changes']}", flush=True)
        return result

    PI0Policy.reset, PI0Policy.prepare_state = reset, state
    PI0Policy.select_action, PI0Policy._preprocess_images = select, images
    P.E.rollout = roll


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    assert not OUT.exists(), "refusing to overwrite state evidence"
    atexit.register(P._save)
    P.E.preprocess_observation = P.pre
    P._log_masks()
    P._delta_ref()
    install()
    sys.exit(P.E.main())
