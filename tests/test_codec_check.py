"""Codec failure propagation and ownership without invoking a real codec."""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/checks/codec_check.py"


@pytest.mark.parametrize("failure", ["none", "decoder", "short_decode", "encoder"])
def test_codec_check_owns_only_its_temporary_clip(tmp_path, monkeypatch, failure):
    spec = importlib.util.spec_from_file_location("codec_check", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    sentinel = tmp_path / "codec_test.mp4"
    sentinel.write_bytes(b"existing clip")
    paths = []

    class Container:
        def __init__(self, path, mode):
            paths.append(Path(path))
            Path(path).write_bytes(b"new clip")

        def __enter__(self): return self
        def __exit__(self, *args): pass
        def add_stream(self, *args, **kwargs):
            return SimpleNamespace(encode=lambda *args: [], codec_context=SimpleNamespace(name="fixture"))

    def encoders(*args, **kwargs):
        if failure == "encoder":
            raise subprocess.CalledProcessError(1, "ffmpeg")
        return SimpleNamespace(stdout="libsvtav1")

    class Decoder:
        def __init__(self, path):
            assert Path(path).read_bytes() == b"new clip"
            if failure == "decoder":
                raise RuntimeError("decoder unavailable")

        def __getitem__(self, key):
            return SimpleNamespace(data=np.zeros((4 if failure == "short_decode" else 5, 3, 96, 128), dtype=np.uint8))

    monkeypatch.setitem(sys.modules, "av", SimpleNamespace(open=Container, __version__="fixture",
                        VideoFrame=SimpleNamespace(from_ndarray=lambda *args, **kwargs: None)))
    monkeypatch.setitem(sys.modules, "torchcodec.decoders", SimpleNamespace(VideoDecoder=Decoder))
    monkeypatch.setattr(module.subprocess, "run", encoders)
    assert module.main() == (0 if failure == "none" else 1)
    assert sentinel.read_bytes() == b"existing clip"
    assert list(tmp_path.iterdir()) == [sentinel]
    assert all(path.parent != tmp_path for path in paths)
