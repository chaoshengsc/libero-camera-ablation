"""Encode/decode a temporary clip; any failed stage returns nonzero."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    try:
        import av
        import numpy as np
        from torchcodec.decoders import VideoDecoder

        enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True, check=True).stdout
        print("libsvtav1 encoder:", "libsvtav1" in enc)
        # Own both the directory and the clip; never touch a caller's codec_test.mp4.
        with tempfile.TemporaryDirectory(prefix="codec_check_", dir=os.environ.get("TMPDIR")) as directory:
            path = Path(directory) / "clip.mp4"
            frames = (np.random.rand(30, 96, 128, 3) * 255).astype(np.uint8)
            with av.open(str(path), "w") as container:
                stream = container.add_stream("libsvtav1" if "libsvtav1" in enc else "libx264", rate=30)
                stream.width, stream.height, stream.pix_fmt = 128, 96, "yuv420p"
                for frame in frames:
                    for packet in stream.encode(av.VideoFrame.from_ndarray(frame, format="rgb24")):
                        container.mux(packet)
                for packet in stream.encode():
                    container.mux(packet)
            print("av", av.__version__, "encoded", path.stat().st_size, "B with", stream.codec_context.name)
            decoder = VideoDecoder(str(path))
            decoded = decoder[0:5].data
            if decoded.shape[0] != 5:
                raise ValueError("Expected five decoded frames")
            print("torchcodec OK", decoded.shape, decoded.dtype)
        return 0
    except Exception as error:
        print(f"codec FAIL {type(error).__name__}: {str(error)[:400]}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
