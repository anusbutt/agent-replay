# AMD Compute — AgentReplay's analysis pipeline on Radeon gfx1100 via ROCm

This directory is the committed evidence that AgentReplay's root-cause
analysis ran on **AMD hardware**: the production analysis prompt, imported
unmodified from [`app/analysis/prompts.py`](../app/analysis/prompts.py),
executed against the real recorded Friday/Saturday misbooking run on an
**AMD Radeon gfx1100** (RDNA3, 48GB VRAM) through **PyTorch built for
ROCm** on the hackathon's AMD compute pod.

The model loaded on the AMD GPU is defined by `MODEL_ID` in
[`run_analysis_on_amd.py`](run_analysis_on_amd.py) —
**Qwen/Qwen2.5-1.5B-Instruct**. A smaller model was chosen because the
pod's 24-hour window and download bandwidth made the ~50GB Gemma 4 26B
weights infeasible; the requirement being demonstrated is AMD compute
usage, not model scale. The public hosted demo serves the same analysis
pipeline through Gemma 4 on OpenRouter (see the
[root README](../README.md#amd-compute-usage)).

## How to reproduce

On a machine with an AMD GPU, ROCm, and a ROCm build of PyTorch
(plus `transformers`), from the repo root:

```bash
python amd/run_analysis_on_amd.py
```

The script refuses to run on a CUDA build (`torch.version.hip` must be
populated and `torch.version.cuda` must be `None`), loads the model in
float16 onto the GPU, runs greedy decoding, captures `rocm-smi` **while
the model is resident in VRAM**, and overwrites the five artifacts below.

## The artifacts

| File | What it is | What it proves |
|---|---|---|
| [`run_analysis_on_amd.py`](run_analysis_on_amd.py) | The exact script executed on the AMD pod. Imports `build_analysis_messages` + `extract_json_object` unmodified from `app/analysis/prompts.py`; loads the Friday/Saturday fixture from `scripts/seed_demo_run.py::BATCH`; hard-asserts a ROCm torch build | The evidence is reproducible and uses AgentReplay's real production prompt and real recorded data — not a synthetic hello-world |
| [`environment.txt`](environment.txt) | `torch.__version__`, `torch.version.hip`, `torch.version.cuda` (None), `gcnArchName`, total VRAM, `MODEL_ID`, captured at run time | The PyTorch stack was a ROCm build talking to a gfx1100 device — not CUDA, not CPU |
| [`prompt.txt`](prompt.txt) | The exact prompt string sent to the model: the analysis system prompt from `app/analysis/prompts.py` + the serialized fixture transcript, rendered through the model's chat template | What ran on AMD is the same root-cause prompt the hosted product sends to its judge |
| [`verdict.json`](verdict.json) | Machine-readable result: `model_id`, `hardware`, `rocm_version`, `fixture`, `timestamp_utc`, verbatim `raw_output`, and `parsed` (the `{failing_step, root_cause, suggested_fix}` schema used at `run_metadata.analysis`, or null if the model's JSON didn't validate) | The AMD run produced a real verdict in the product's own schema, with full provenance |
| [`verdict.md`](verdict.md) | The same verdict, human-readable, with a hardware/model/fixture header | A judge can read the outcome without parsing JSON |
| [`rocm_smi_during_inference.txt`](rocm_smi_during_inference.txt) | `rocm-smi` (plus `--showmeminfo vram`) captured after generation while the model was still resident, plus `torch.cuda.memory_allocated()` | The gfx1100 device actually held the model in VRAM — the card wasn't idle |
