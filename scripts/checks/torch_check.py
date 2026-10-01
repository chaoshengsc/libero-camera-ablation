import time

import torch

print("torch", torch.__version__, "cuda", torch.version.cuda, "cudnn", torch.backends.cudnn.version())
print("available", torch.cuda.is_available(), torch.cuda.get_device_name(0))
a = torch.randn(4096, 4096, device="cuda"); b = torch.randn(4096, 4096, device="cuda")
torch.cuda.synchronize(); t = time.time()
for _ in range(20): c = a @ b
torch.cuda.synchronize(); dt = time.time() - t
print(f"matmul fp32 ~{20*2*4096**3/dt/1e12:.1f} TFLOPS, checksum ok={torch.isfinite(c).all().item()}")
print("mem used MiB", torch.cuda.max_memory_allocated() // 2**20)
