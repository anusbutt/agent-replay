# AMD Compute — Gemma 4 on Radeon (gfx1100) via ROCm

This directory is the committed evidence that AgentReplay's analysis
pipeline ran on **AMD hardware**: **Gemma 4 26B** loaded onto an **AMD
Radeon (gfx1100)** GPU through **ROCm** (torch + ROCm) on the AMD compute
pod provided by the hackathon, producing the same root-cause analysis
verdict the product stores at `run_metadata.analysis`.

## What lives here

| File | What it is |
|---|---|
| [`run_gemma_analysis.py`](run_gemma_analysis.py) | The script executed on the AMD pod: loads Gemma 4 26B via torch/ROCm on the gfx1100 device, feeds it the serialized failing run, prints the verdict JSON |
| [`analysis_prompt.txt`](analysis_prompt.txt) | The real analysis prompt sent to the model — the serialized Nestaro Friday/Saturday run plus AgentReplay's root-cause instruction (same prompt builder as `app/analysis/prompts.py`) |
| [`gemma4_verdict_on_amd.json`](gemma4_verdict_on_amd.json) | The verdict Gemma 4 produced on the AMD GPU: `failing_step`, `root_cause`, `suggested_fix` — matching the schema stored at `run_metadata.analysis` |
| [`rocm_smi_during_inference.txt`](rocm_smi_during_inference.txt) | `rocm-smi` output captured **while inference was running**: shows the gfx1100 device with VRAM occupied by the loaded model |

## How this relates to the hosted demo

The public demo (Vercel dashboard + Railway backend) serves analysis
through OpenRouter for always-on availability — an OpenAI-compatible
endpoint selected by `ANALYSIS_BASE_URL`/`ANALYSIS_API_KEY`/
`ANALYSIS_MODEL` env vars. The run documented here executed the same
analysis (same prompt shape, same verdict schema) directly on AMD silicon
via ROCm.
