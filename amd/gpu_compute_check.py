"""GPU compute check run on the AMD Developer Cloud hackathon pod.

Verifies the PyTorch stack is a ROCm build (not CUDA), prints the device
identity, and executes real GPU compute: a 4096x4096 matmul on the AMD
device. Output captured in gpu_compute_check_output.txt.

Runnable standalone on any ROCm machine:  python amd/gpu_compute_check.py
"""

import torch

assert torch.version.hip, f"not a ROCm build: torch.version.hip={torch.version.hip!r}"
assert torch.version.cuda is None, f"CUDA build detected: torch.version.cuda={torch.version.cuda!r}"
assert torch.cuda.is_available(), "no ROCm device visible to torch"

props = torch.cuda.get_device_properties(0)
# get_device_name() returns an empty string on this RDNA3 card — gcnArchName
# is the authoritative identifier.
print(f"name: {props.name!r} | gcn: {props.gcnArchName} | VRAM GB: {props.total_memory / 2**30:.1f}")

torch.manual_seed(0)
a = torch.randn(4096, 4096, device="cuda")
b = torch.randn(4096, 4096, device="cuda")
c = a @ b
torch.cuda.synchronize()
print(f"matmul OK: {c.sum().item()}")
print(f"alloc MB: {torch.cuda.memory_allocated() // 2**20}")
