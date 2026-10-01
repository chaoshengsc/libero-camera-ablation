import os
import subprocess

import numpy as np

p = os.environ["TMPDIR"] + "/codec_test.mp4"
frames = (np.random.rand(30, 96, 128, 3) * 255).astype(np.uint8)
enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
print("libsvtav1 encoder:", "libsvtav1" in enc)
import av

with av.open(p, "w") as c:
    s = c.add_stream("libsvtav1" if "libsvtav1" in enc else "libx264", rate=30); s.width, s.height, s.pix_fmt = 128, 96, "yuv420p"
    for f in frames:
        for pk in s.encode(av.VideoFrame.from_ndarray(f, format="rgb24")): c.mux(pk)
    for pk in s.encode(): c.mux(pk)
print("av", av.__version__, "encoded", os.path.getsize(p), "B with", s.codec_context.name)
try:
    from torchcodec.decoders import VideoDecoder
    d = VideoDecoder(p); x = d[0:5].data
    print("torchcodec OK", x.shape, x.dtype)
except Exception as e:
    print("torchcodec FAIL", type(e).__name__, str(e)[:400])
os.remove(p)
