# AMD Compute — AgentReplay on Radeon gfx1100 (RDNA3) via ROCm

AgentReplay's ROCm/PyTorch stack was brought up on an **AMD Radeon gfx1100**
(RDNA3, 48GB) on the **AMD Developer Cloud hackathon pod**.
`torch.version.hip` is populated and `torch.version.cuda` is `None`: this is
a **ROCm** build of **PyTorch**, not CUDA. **GPU compute was executed and
verified** (a 4096x4096 matmul on the AMD device — see the captured output
below).

**The full analysis pipeline executed on the pod on 2026-07-11** via
[`run_analysis_on_amd_standalone.py`](run_analysis_on_amd_standalone.py):
AgentReplay's real, unmodified root-cause prompt (byte-identical embed of
`app/analysis/prompts.py`, drift-guarded by
`tests/test_amd_standalone_embeds.py`) over the real Nestaro Friday/Saturday
misbooking fixture, with inference on **google/gemma-3-4b-it** loaded in
float16 and resident in VRAM on the gfx1100 (8.08 GB allocated; `rocm-smi`
captured mid-run, non-idle). The model's raw output was **not valid verdict
JSON** (see [`verdict.md`](verdict.md) — `parsed: null`), so no parsed
failing-step verdict was produced on AMD; what this directory demonstrates
is the real AMD inference path — real prompt, real fixture, real GPU — not
the verdict itself.

The public hosted demo serves root-cause analysis via OpenRouter, which is
provider-swappable through `ANALYSIS_BASE_URL` / `ANALYSIS_API_KEY` /
`ANALYSIS_MODEL`. The hosted demo does not run on AMD; the evidence in this
directory is what ran on AMD.

## The files

| File | What it is | What it proves | How to reproduce |
|---|---|---|---|
| [`environment.txt`](environment.txt) | Environment fingerprint written by the standalone run: torch 2.9.1 ROCm build (`torch.version.hip` = 7.2.53211, `torch.version.cuda` = None), gfx1100, 48 GB VRAM, MODEL_ID | The PyTorch stack talking to the GPU was a ROCm build on a gfx1100 device | `python amd/run_analysis_on_amd_standalone.py` on a ROCm machine |
| [`rocm_smi.txt`](rocm_smi.txt) | `rocm-smi` capture from the pod taken before model load (GPU idle): device 0x744b, 241W power cap | The physical AMD device present on the pod, as reported by ROCm's own tooling | Run `rocm-smi` on the pod |
| [`gpu_compute_check.py`](gpu_compute_check.py) | Script that asserts a ROCm (non-CUDA) torch build, prints device identity, and executes a 4096x4096 matmul on the AMD device | Real GPU compute ran through ROCm — not just an environment listing | `python amd/gpu_compute_check.py` on any ROCm machine |
| [`gpu_compute_check_output.txt`](gpu_compute_check_output.txt) | Captured output of that script on the pod: gfx1100, matmul result, VRAM allocated. `get_device_name()` returns empty on this RDNA3 card — `gcnArchName` is the authoritative identifier | The compute check succeeded on the AMD GPU | Same command; the matmul sum is seed/platform-dependent |
| [`run_analysis_on_amd_standalone.py`](run_analysis_on_amd_standalone.py) | The self-contained script **executed on the pod on 2026-07-11**: embeds the real prompt + fixture (drift-guarded by tests), hard-asserts a ROCm build, loads gemma-3-4b-it in float16, greedy-decodes, captures `rocm-smi` while the model is resident | The real analysis prompt and real recorded fixture ran through live inference on the AMD GPU | `python amd/run_analysis_on_amd_standalone.py` on a ROCm machine with the model in the local HF cache |
| [`prompt.txt`](prompt.txt) | The exact prompt string sent to the model on the pod: the analysis system prompt + serialized fixture transcript, rendered through the model's chat template | What ran on AMD is the same root-cause prompt the hosted product sends to its judge | Written by the standalone run |
| [`rocm_smi_during_inference.txt`](rocm_smi_during_inference.txt) | `rocm-smi` captured after generation while gemma-3-4b-it was still resident (VRAM 18%, MCLK 1124MHz, `torch.cuda.memory_allocated()` = 8.08 GB) | The gfx1100 actually held the model in VRAM during the run — the card was not idle | Written by the standalone run |
| [`verdict.json`](verdict.json) | Machine-readable result of the pod run with full provenance. `raw_output` is empty and `parsed` is `null` — the model did not return valid verdict JSON | Honest record of the run's outcome: inference executed on AMD; no parsed verdict was produced | Written by the standalone run |
| [`verdict.md`](verdict.md) | The same outcome, human-readable, with the hardware/model/fixture header | A judge can read the outcome without parsing JSON | Written by the standalone run |
| [`run_analysis_on_amd.py`](run_analysis_on_amd.py) | The repo-importing variant of the runner (imports `app/analysis/prompts.py` and the fixture directly rather than embedding them) | The same pipeline is reproducible from the repo itself | `python amd/run_analysis_on_amd.py` from the repo root (torch ROCm build + transformers) |
