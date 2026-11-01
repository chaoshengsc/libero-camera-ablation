# Official OpenPI π0: installation and reproduction

[中文](OPENPI_CN.md) · [Installation](INSTALL.md) · [Scripts](../scripts/README.md) · [Results](EXPERIMENTS.md#15-official-π0-control)

This guide reconstructs the **native OpenPI/JAX server + LeRobot LIBERO client** used on 2026-10-28–29. It is the path that passed acceptance: smoke **50/50**, then normal **482/500 = 96.4%**. The LeRobot conversion scored **0/50** in its smoke test and is retained as a failed path, not an installation prerequisite.

It reproduces this repository's historical client protocol: **280 control steps plus ten settling steps** for Spatial. The pinned [upstream OpenPI example](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/examples/libero/main.py) uses 220 plus ten. The 96.4% result evaluates official weights under our protocol, rather than reproducing the 96.8% reference under identical conditions; see [protocols and audit scope](EXPERIMENTS.md#3-evaluation-protocols-and-audit-scope).

The commands below document setup and execution; they were **not executed again while writing this guide**. Read-only checks on 2026-11-01 verified installed package metadata, selected source fingerprints, the client configuration and historical logs. A clean-machine installation and a new model/simulation run remain unverified. Recovery experiments and P3 remain paused.

## 1. Recorded configuration

| Component | Recorded value |
|---|---|
| Workstation | Ubuntu 24.04, RTX A5000 24 GB, driver 570; no sudo or apt |
| OpenPI source | [`215abfb217dbac7d5f1273282331b9b1866c0479`](https://github.com/Physical-Intelligence/openpi/tree/215abfb217dbac7d5f1273282331b9b1866c0479) |
| Server environment | Python 3.11.18; uv 0.9.5; `uv sync --frozen` |
| Installed JAX packages | jax / jaxlib / jax-cuda12-plugin / jax-cuda12-pjrt 0.5.3 |
| Other installed server packages | flax 0.10.2; orbax-checkpoint 0.11.13; NumPy 1.26.4; tensorstore 0.1.74; ml-dtypes 0.4.1 |
| Client environment | `smolvla`: LeRobot v0.6.1 (`7e241bd6`), torch 2.11.0+cu128, MuJoCo 3.3.2, robosuite 1.4.0, hf-libero 0.1.4 |
| Native checkpoint | `gs://openpi-assets/checkpoints/pi0_libero`; historical download: 19 files, 12,014,131,888 bytes |
| Evaluation | LIBERO-Spatial, ten tasks, batch1, seed1000, 280 control steps + ten settling steps, five executed actions per query |
| Images | Historical main run: 256 rendering, then 224 model input; separate 360-rendering check |

The server and client use **separate environments**. OpenPI's lock includes its own Git-pinned LeRobot dependency; it is not the v0.6.1 simulation client. The October 1 [environment exports](../env/lock/) do not include OpenPI.

Source fingerprints, matched to the pinned upstream files:

| File | SHA256 |
|---|---|
| `uv.lock` | `793488b5a55bb87200db90a61fd0af51922b686d94e1da4f4c587ab119b37d74` |
| `pyproject.toml` | `e1f457bd81622a47a4c4de17b92815977ac5fcd40116bec92398eb400bf76483` |

The historical source directory is `src/openpi@215abfb2`, with no `.git` directory. Selected file fingerprints match upstream; this is not verification of a live Git HEAD or of every source file. The new-clone recipe below retains Git metadata.

## 2. Prepare the separate server environment

First complete the [working-directory setup](INSTALL.md#0-working-directory-and-miniforge) and the [`smolvla` client environment](INSTALL.md#3-smolvla-environment-smolvla-π0-π05-shared-by-evaluation-and-training). Cache the LIBERO task/initial-state assets before an offline evaluation. This guide does not install the upstream LIBERO example's separate Python 3.8 environment.

Use Bash on the Linux workstation. In each terminal, set `REPO` to this checkout's absolute path and `EMB_ROOT` to the isolated working directory. For a new setup:

```bash
source "$EMB_ROOT/env.sh"
export OP_REV=215abfb217dbac7d5f1273282331b9b1866c0479
export OP_SRC="$EMB_ROOT/src/openpi@215abfb2"
export OP_ENV="$EMB_ROOT/envs/openpi"
export OP_PY="$EMB_ROOT/envs/openpi_py311/bin/python"
export OP_UV="$EMB_ROOT/envs/openpi_py311/bin/uv"
export UV_CACHE_DIR="$EMB_ROOT/cache/uv"
export UV_PYTHON="$OP_PY" UV_PYTHON_DOWNLOADS=never
export UV_PROJECT_ENVIRONMENT="$OP_ENV" GIT_LFS_SKIP_SMUDGE=1
export OPENPI_DATA_HOME="$EMB_ROOT/cache/openpi"
```

These variables keep the Python base, uv environment, downloads and cache under `EMB_ROOT`. `env.sh` alone does not set `UV_*` or `OPENPI_DATA_HOME`. Reuse an existing accepted installation; do not rerun the creation commands over it.

**Writes environments and downloads packages.** From any directory, create the Python base and install the recorded uv version:

```bash
conda create -y -p "$EMB_ROOT/envs/openpi_py311" -c conda-forge python=3.11.18
"$OP_PY" -m pip install uv==0.9.5
```

`conda` must come from the Miniforge setup above. If the recorded version cannot be resolved, stop and record the failure rather than silently changing Python or the lock. Historical logs used `python=3.11`, which resolved to 3.11.18; the recipe now states that resolved version explicitly.

Git must be available for cloning and uv's Git dependencies. The workstation used the Git already installed in the `lerobot` environment; it was absent from the default SSH PATH. Use that existing executable if needed, without installing system packages:

```bash
export PATH="$EMB_ROOT/envs/lerobot/bin:$PATH"
git --version
git clone https://github.com/Physical-Intelligence/openpi.git "$OP_SRC"
git -C "$OP_SRC" checkout --detach "$OP_REV"
cd "$OP_SRC"
sha256sum uv.lock pyproject.toml
"$OP_UV" sync --frozen
```

Check the two hashes against section 1 **before** syncing. The source target must be unused. `sync --frozen` installs into `OP_ENV`, including editable OpenPI/openpi-client; it does not activate the client environment. A successful install is not proof of GPU inference. Do not apply the upstream PyTorch `transformers_replace` patch to this JAX path or install server packages into `smolvla`.

## 3. Native weights, normalization and tokenizer

**Downloads weights; no inference.** After preparing a fresh checkpoint target, run from any directory:

```bash
export OP_CKPT="$EMB_ROOT/ckpt/openpi_pi0_libero"
mkdir -p "$EMB_ROOT/ckpt"
"$OP_PY" "$REPO/scripts/openpi/download_checkpoint.py" \
  checkpoints/pi0_libero "$OP_CKPT"
```

The [downloader](../scripts/openpi/download_checkpoint.py) uses the public bucket without a Hugging Face token or `gsutil`. Require `DONE all md5 verified`; keep the sibling `openpi_pi0_libero.listing.json`, which records object names, sizes, update times and MD5s. The accepted historical download had 19 files and 12.01 GB. The bucket prefix is mutable, not an immutable model revision: preserve the manifest for the actual download. This documentation pass did not re-hash the 12 GB weights.

An existing matching file is skipped; a mismatching file can be replaced. Do not use this downloader as a read-only verifier of an existing accepted checkpoint, and do not refresh an old manifest in place merely to check installation.

The checkpoint root must contain `params/` and `assets/physical-intelligence/libero/norm_stats.json`. Pass this root, not `params/`, to the server. Native Orbax parameters and their accompanying normalization assets are used together; `model.safetensors` from the LeRobot conversion is not used.

The pinned [OpenPI tokenizer](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/src/openpi/models/tokenizer.py) requests `gs://big_vision/paligemma_tokenizer.model`. With `OPENPI_DATA_HOME` above, its cache location is:

```text
$EMB_ROOT/cache/openpi/big_vision/paligemma_tokenizer.model
```

That file exists in the recorded installation. A new installation may download it when loading the policy. Fully offline startup requires this cache **as well as** the checkpoint. `HF_HUB_OFFLINE=1` does not block OpenPI's GCS downloader. The native server does not need this project's private/gated Hugging Face tokenizer directory; do not copy tokenizer credentials or private material into Git.

## 4. Prepare the client's configuration-only directory

The remote client still parses `--policy.path`, so it needs a valid PI0 `config.json`. The historical directory is `ckpt/pi0_libero_base@98ac51b8_openpi`. With `WRAP=probe` and `POLICY_SERVER` set, [eval_probe.py](../scripts/eval/eval_probe.py) replaces policy creation with the remote proxy and pre/postprocessing with identities: it does **not** load the conversion's PyTorch weights or processor files.

For a new setup, the following downloads **only the small public configuration**, changes its dtype field as in the historical copy, and refuses an existing target. It is reconstructed from source and hash-checked, not a fresh-machine model test. Skip it when reusing the accepted directory.

```bash
export OP_CLIENT="$EMB_ROOT/ckpt/pi0_libero_base@98ac51b8_openpi"
"$OP_PY" - <<'PY'
import hashlib
import json
import os
import urllib.request
from pathlib import Path

rev = "98ac51b805725b9f6cc90ad0b92b8b8ecbefa9eb"
url = f"https://huggingface.co/lerobot/pi0_libero_base/resolve/{rev}/config.json"
with urllib.request.urlopen(url, timeout=60) as response:
    raw = response.read()
expected = "80b51238a53ccd8421577e94f39c201915b805c849989558f3c0af410b9a2a5c"
if hashlib.sha256(raw).hexdigest() != expected:
    raise SystemExit("Unexpected source configuration; stop and retain the evidence")
cfg = json.loads(raw)
cfg["dtype"] = "bfloat16"
text = json.dumps(cfg, indent=4)
expected = "2405b602e3b4f3fe8f5e2239e8fa74fad0e69650af2b0fdf8af1c17798669e90"
if hashlib.sha256(text.encode()).hexdigest() != expected:
    raise SystemExit("Configuration differs from the recorded client")
target = Path(os.environ["OP_CLIENT"])
target.mkdir(parents=True, exist_ok=False)
with (target / "config.json").open("x") as output:
    output.write(text)
print("Configuration matches the recorded client")
PY
```

Expected fields: `type=pi0`, `chunk_size=50`, two `[3,256,256]` images, state `[8]`, action `[7]`. The CLI overrides the stored `n_action_steps=10` to **5**. The dtype field describes this configuration; the native model uses OpenPI's own config. Do not run `adapt_openpi_pi0.py` or download conversion weights just to supply this proxy configuration.

## 5. Start the local server, then the client

**Starts GPU inference and simulation.** These are execution instructions, not work performed during this documentation update. Use two terminals on the same workstation. Check that no existing job/server already owns the chosen port; do not start a duplicate or stop another user's process.

### Terminal A: server

Restore the section 2 variables, set `OP_CKPT` as in section 3, and load `env.sh`. Create the shared local authentication file **once**, only when it does not already exist:

```bash
"$OP_PY" - <<'PY'
import os
import secrets
from pathlib import Path

os.umask(0o077)
key = Path(os.environ["EMB_ROOT"]) / "tmp/openpi_authkey"
with key.open("x") as output:
    output.write(secrets.token_hex(32))
PY
```

An existing file causes an error; reuse its contents rather than regenerate it while a server/client is using it. Confirm it is readable and nonempty; if reading fails, stop before launching either process. Do not enable shell tracing or print the key. Start the server in the foreground:

```bash
export OPENPI_PORT=18765
export OPENPI_AUTHKEY="$(cat "$EMB_ROOT/tmp/openpi_authkey")"
"$OP_ENV/bin/python" -u "$REPO/scripts/openpi/serve_pi0_libero.py" \
  "$OP_CKPT" "$OPENPI_PORT"
```

Expect `loaded ... pi0_libero` configuration information and `ready on port 18765`. This proves loading/listening, not successful rollout. The first inference may include JAX compilation. Preserve stdout in a new log if recording a run. The [bridge](../scripts/openpi/serve_pi0_libero.py) uses authenticated `multiprocessing.connection` on **127.0.0.1**, not upstream OpenPI's WebSocket server; do not substitute `serve_policy.py` or expose this port externally.

### Terminal B: client

Set `REPO` and `EMB_ROOT` again, then use an unused run name:

```bash
source "$EMB_ROOT/env.sh"
export OPENPI_PORT=18765
export OPENPI_AUTHKEY="$(cat "$EMB_ROOT/tmp/openpi_authkey")"
CK="$EMB_ROOT/ckpt/pi0_libero_base@98ac51b8_openpi"
RUN=ojx_smoke_check_01
WRAP=probe BLACKOUT=none POLICY_SERVER="$OPENPI_PORT" \
  bash "$REPO/scripts/eval/run_libero.sh" "$RUN" 5 "$CK" 1 \
  --policy.n_action_steps=5 \
  --env.observation_height=256 --env.observation_width=256
```

The wrapper activates `smolvla`, requires cached assets (`HF_HUB_OFFLINE=1`), and runs **five episodes per task, 50 total**, with batch1 and seed1000. `POLICY_SERVER` selects native OpenPI inference; omitting it selects the failed conversion path for this configuration. Existing output directories/files/symlinks are rejected and failed outputs retained. Do not delete an old run to bypass protection.

Within each task, the recorded protocol uses initial-state indices0–4 for smoke,0–49 for the gate and0–9 for 100-episode conditions. The client allows 280 control steps plus ten separate settling steps, differing from the upstream example's 220 control steps. The evaluation seed does not fix the separate OpenPI server's random-number stream.

The client rotates both views by 180°, sends raw eight-dimensional state and task text; the server resizes to 224, applies the original normalization and restores delta actions. It returns `(50,7)` action chunks; only the first five actions are executed before querying again. Do not apply LeRobot normalization or delta restoration a second time.

## 6. Stages and acceptance

[run_official_pi0.sh](../scripts/eval/run_official_pi0.sh) packages historical stages. It reads the port/key settings in [common.sh](../scripts/common.sh), but does not start the server. Its run names are fixed and reject reuse. For a new independently authorized repetition, use fresh names through `run_libero.sh` as above, preserving each condition's episode count and arguments.

| Stage | Run names | Total episodes per run / rendering |
|---|---|---|
| `smoke` | `ojx_smoke` | 50 / 256 |
| `gate` | `ojx_none` | 500 / 256 |
| `ablation` | `ojx_all`, `ojx_drop_all`, `ojx_freeze` | 100 each / 256; also `pi0_drop_all`, 100 / 360 through **LeRobot v044**, without the server |
| `single` | `ojx_drop_wrist`, `ojx_drop_agent` | 100 each / 256 |
| `freeze_wrist` | `ojx_freeze_wrist` | 100 / 256 |
| `res360` | `ojx360_none`, `ojx360_all`, `ojx360_drop_all` | 100 each / 360 |
| `replay` | `ojx360_replay`, then its `replay.json` | 100 source episodes / 360, then fixed-action replay without a policy |
| `conv_smoke`, `conv_diag` | `opi0_*` | Failed conversion diagnostics; excluded from the accepted native path |

`ablation` also requires the separate LeRobot v044 checkpoint; the configuration-only directory above does not supply it. Historical replay is not P2: [P2](../scripts/README.md#state-input-and-replay-follow-ups) reuses bundled frozen actions and needs no OpenPI server or new source generation.

Acceptance is more than a successful command:

1. Require shell exit0 and `exit=0` in `$EMB_ROOT/logs/eval/$RUN/stdout.log`. A missing/nonzero code is a technical failure; retain its artifacts.
2. Check `out/eval_info.json` for all ten tasks and the expected episodes per task. Keep `traj.npz`: the wrapper stores first-frame hashes in `h0` and stepwise end-effector records in `eef_*`; historical `first_frame_hash.json`/`first_eef.json` were exports, not extra files automatically written by this entry. Native 256 and LeRobot 360 images cannot share frame hashes; the recorded cross-resolution matching check used first-step end-effector positions, not complete simulator states.
3. Inspect `[probe] remote:` for image `(224,224,3)`, chunk `(50,7)` and actual masks. Normally `base_0_rgb`/`left_wrist_0_rgb` are true and unused `right_wrist_0_rgb` false. `drop_all` makes all three false; black images retain present-camera masks. Frozen images use the real first frame with masks true. These are different interventions.
4. Review the normal **500-episode gate ≥92% manually** before interpreting ablations. Change the example's per-task count from5 to50 and choose another unused name. The stage runner propagates command failures, but **does not enforce the success-rate threshold**. Do not repeat or discard states until a desired score appears.

The accepted historical native results include smoke50/50, gate482/500, 256 all-black0/100 and both-slots-masked0/100; see the [full table and limits](EXPERIMENTS.md#15-official-π0-control) and [raw records](../dashboard/data/official_pi0/). A native action outside `[-1,1]` alone is not a failed gate: that earlier rule was corrected in the log. Do not add extra clipping to force it to pass.

At 100 episodes, conditions reuse the first ten initial states per task; the normal matched subset is93/100, not the full gate's96.4%. Keep matched comparisons and the separate360 results distinct. The server's random-number stream and other nondeterminism do not promise identical scores on repetition. These results do not isolate weights from inference-pipeline differences or identify the mechanism of LeRobot v044's retained success.

## 7. Failure checks and evidence

| Symptom | Check before another launch |
|---|---|
| `git` missing during setup | Check PATH; historical installation reused `envs/lerobot/bin/git` |
| `openpi` import fails | Use `OP_ENV/bin/python`, verify editable source location and frozen install; do not install into the client |
| Offline policy load stalls/fails | Check native params/norm assets and the separate OpenPI tokenizer cache; HF offline mode is insufficient |
| Connection refused/authentication failure | Check the existing server's readiness, matching local port and shared key file without printing it |
| `Address already in use` | Find the existing owner; do not start a duplicate or kill another job |
| Output already exists | Choose a fresh name; preserve old/failed records |
| Native-client log lacks `remote:` evidence | Check `WRAP=probe`, `POLICY_SERVER`, batch1 and the valid client config; do not accept it as native OpenPI |
| Low success despite exit0 | Audit coverage, versions, image/mask evidence and preprocessing; retain the negative result rather than relabeling it as reproduction |

These are source-based checks, not claims that every listed failure occurred in a new run. GPU memory availability and a clean-machine startup have not been revalidated by this documentation pass.

Historical installation/download/server logs were kept under `$EMB_ROOT/logs/official/`; the download listing is beside the checkpoint. Public evidence is in the [experiment log](NOTES.md), [official results CSV](../results/official_pi0_summary.csv) and [raw JSONs](../dashboard/data/official_pi0/). Full weights, keys, tokenizer files and private logs are not bundled in Git. To recompute public tables without a model or simulation, follow the [CPU quick start](../README.md#quick-start).

Pinned upstream references: [installation and JAX/PyTorch distinction](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/README.md), [dependency definitions](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/pyproject.toml), [lock](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/uv.lock), [LIBERO example](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/examples/libero/README.md), [cache handling](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/src/openpi/shared/download.py), [source client config](https://huggingface.co/lerobot/pi0_libero_base/blob/98ac51b805725b9f6cc90ad0b92b8b8ecbefa9eb/config.json).
