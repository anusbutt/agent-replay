# AMD Compute — AgentReplay on Radeon gfx1100 (RDNA3) via ROCm

AgentReplay's ROCm/PyTorch stack was brought up on an **AMD Radeon gfx1100**
(RDNA3, 48GB) on the **AMD Developer Cloud hackathon pod**.
`torch.version.hip` is populated and `torch.version.cuda` is `None`: this is
a **ROCm** build of **PyTorch**, not CUDA. **GPU compute was executed and
verified** (a 4096x4096 matmul on the AMD device — see the captured output
below).

An on-pod run of the full analysis prompt was prepared
([`run_analysis_on_amd.py`](run_analysis_on_amd.py)) but the pod's gateway
became unavailable before it executed; the script is committed and
reproducible on any ROCm machine.

The public hosted demo serves root-cause analysis via OpenRouter, which is
provider-swappable through `ANALYSIS_BASE_URL` / `ANALYSIS_API_KEY` /
`ANALYSIS_MODEL`. The hosted demo does not run on AMD; the evidence in this
directory is what ran on AMD.

## The files

| File | What it is | What it proves | How to reproduce |
|---|---|---|---|
| [`environment.txt`](environment.txt) | Environment fingerprint captured on the pod: torch 2.9.1 ROCm build (`torch.version.hip` = 7.2.53211, `torch.version.cuda` = None), gfx1100, 51.5 GB VRAM | The PyTorch stack talking to the GPU was a ROCm build on a gfx1100 device | Print `torch.__version__`, `torch.version.hip`, `torch.version.cuda`, `torch.cuda.get_device_properties(0)` on any ROCm machine |
| [`rocm_smi.txt`](rocm_smi.txt) | `rocm-smi` capture from the pod (taken before model load — GPU idle): device 0x744b, 241W power cap | The physical AMD device present on the pod, as reported by ROCm's own tooling | Run `rocm-smi` on the pod |
| [`gpu_compute_check.py`](gpu_compute_check.py) | Script that asserts a ROCm (non-CUDA) torch build, prints device identity, and executes a 4096x4096 matmul on the AMD device | Real GPU compute ran through ROCm — not just an environment listing | `python amd/gpu_compute_check.py` on any ROCm machine |
| [`gpu_compute_check_output.txt`](gpu_compute_check_output.txt) | Captured output of that script on the pod: gfx1100, matmul result, VRAM allocated. `get_device_name()` returns empty on this RDNA3 card — `gcnArchName` is the authoritative identifier | The compute check succeeded on the AMD GPU | Same command; the matmul sum is seed/platform-dependent |
| [`run_analysis_on_amd.py`](run_analysis_on_amd.py) | The prepared full-pipeline run: imports AgentReplay's real analysis prompt unmodified from `app/analysis/prompts.py`, loads the real Friday/Saturday fixture, hard-asserts a ROCm build, and writes verdict + VRAM-capture artifacts. Not executed — the pod's gateway went down first | The intended end-to-end demonstration is committed, auditable, and runnable by anyone with a ROCm machine | `python amd/run_analysis_on_amd.py` from the repo root (torch ROCm build + transformers) |
