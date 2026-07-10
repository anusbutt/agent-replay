---
id: 0019
title: AMD run script and model claim fix
stage: misc
date: 2026-07-10
surface: agent
model: claude-fable-5
feature: 001-agentreplay-v1
branch: main
user: anusbutt
command: none
labels: ["amd", "rocm", "hackathon", "evidence", "docs"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - README.md
 - CLAUDE.md
 - .specify/memory/constitution.md
 - specs/001-agentreplay-v1/research.md
 - amd/README.md
 - amd/run_analysis_on_amd.py
 - amd/environment.txt
 - amd/prompt.txt
 - amd/verdict.json
 - amd/verdict.md
 - amd/rocm_smi_during_inference.txt
tests:
 - python3 -m py_compile amd/run_analysis_on_amd.py (passes)
 - module import + transcript/prompt/schema checks with stubbed torch (passes)
 - repo-wide grep: only remaining "Gemma 4 26B" mention is the truthful infeasibility sentence
---

## Prompt

Three tasks. Do them in order. Commit at the end.

TASK 1 — Correct a false claim before it ships.
The README "AMD Compute Usage" section says "Gemma 4 26B". That is wrong.
Gemma 4 26B was never loaded — it was ruled out (50GB download, infeasible in
the pod's time window). The model actually run on AMD is defined by MODEL_ID
in the script you're about to write.

Rewrite the section to be exactly true:
- Analysis inference for the public hosted demo runs Gemma 4 via OpenRouter
  (provider-swappable: ANALYSIS_BASE_URL / ANALYSIS_API_KEY / ANALYSIS_MODEL).
- AMD compute is demonstrated separately in amd/: AgentReplay's real
  root-cause prompt, imported unmodified from app/analysis/prompts.py, was
  executed against a real recorded run on an AMD Radeon gfx1100 (RDNA3, 48GB,
  ROCm 7.2) using PyTorch built for ROCm (torch.version.hip populated,
  torch.version.cuda None).
- State the model actually loaded on AMD, and say in one sentence that a
  smaller model was chosen because the hackathon pod's 24h window and download
  bandwidth made the 26B weights infeasible; the requirement is AMD compute
  usage, not model scale.
- Keep scanner keywords: ROCm, AMD, gfx1100, Radeon, PyTorch. Link to amd/.

Rename placeholders: run_gemma_analysis.py -> run_analysis_on_amd.py,
gemma4_verdict_on_amd.json -> verdict.json. Update amd/README.md references.
Repo-wide grep for "Gemma 4 26B" and "gemma4" outside history/prompts/ and fix.
Leave history/prompts/ untouched — verbatim records, per CLAUDE.md.

TASK 2 — Write amd/run_analysis_on_amd.py.

Constraints:
- MODEL_ID as a module-level constant at the top, single line, easy to swap.
  Set it to "Qwen/Qwen2.5-1.5B-Instruct".
- Import the real prompt builder from app/analysis/prompts.py. Do NOT retype or
  paraphrase the prompt. Read that module first and use its actual function name
  and signature. The point of this artifact is that it is the SAME prompt.
- Load the Friday/Saturday misbooking fixture from wherever it actually lives.
  Find it, don't guess the path.
- Assert torch.version.hip is truthy AND torch.version.cuda is None. Fail loud
  if not — a CUDA build would invalidate the entire artifact.
- Load model to "cuda" (ROCm maps to the cuda device string), dtype float16.
  Not bfloat16 — gfx1100 support is unreliable.
- Run `rocm-smi` via subprocess AFTER the model is resident in VRAM and BEFORE
  the process exits. If it runs after teardown the capture shows an idle card
  and the evidence is worthless. Also record torch.cuda.memory_allocated().
- Greedy decode, do_sample=False, max_new_tokens=512.

Writes into amd/:
  environment.txt  — torch.__version__, torch.version.hip, torch.version.cuda,
                     get_device_properties(0).gcnArchName, total VRAM, MODEL_ID
  prompt.txt       — the exact prompt sent
  verdict.json     — {model_id, hardware, rocm_version, fixture, timestamp_utc,
                      raw_output, parsed} where parsed follows the analysis
                      verdict schema used elsewhere in the codebase if the model
                      returned valid JSON, else null
  verdict.md       — human-readable, with hardware/model/fixture header
  rocm_smi_during_inference.txt — the capture + torch alloc

Print everything to stdout too. Script must be runnable as:
  python amd/run_analysis_on_amd.py
from repo root, with only torch + transformers available. No FastAPI, no DB,
no network beyond the local HF cache.

TASK 3 — Update amd/README.md so each of the five artifacts is described:
what it is, what it proves, how to reproduce.

Then commit everything (including the currently-uncommitted docs pass) in one
commit and push to main.

## Response snapshot

Corrected the "Gemma 4 26B" claim everywhere outside verbatim PHRs: README
AMD section rewritten per spec (OpenRouter demo path; AMD demonstrated in
amd/ with the real prompt from app/analysis/prompts.py on Radeon gfx1100 /
RDNA3 / 48GB / ROCm 7.2 via PyTorch-for-ROCm; model = Qwen2.5-1.5B-Instruct
via MODEL_ID; one-sentence infeasibility rationale for not using 26B;
keywords ROCm/AMD/gfx1100/Radeon/PyTorch present). CLAUDE.md, constitution,
research.md updated to match. Renamed placeholders (run_analysis_on_amd.py,
verdict.json, prompt.txt) and added environment.txt/verdict.md placeholders.
Wrote amd/run_analysis_on_amd.py: MODEL_ID constant, imports
build_analysis_messages + extract_json_object unmodified, loads BATCH
fixture from scripts/seed_demo_run.py (httpx stubbed if absent), hard
ROCm-build assertions, float16 to "cuda", greedy 512 tokens, rocm-smi +
torch.cuda.memory_allocated() captured while model resident, writes all
five artifacts + full stdout log. Verified: py_compile clean; module import
+ transcript format + prompt fidelity + schema validation exercised with
stubbed torch. amd/README.md rewritten: reproduce instructions + per-artifact
what-it-is/what-it-proves table.

## Outcome

- ✅ Impact: AMD evidence pipeline is truthful, reproducible, and scanner-readable; no unbackable claims remain
- 🧪 Tests: py_compile + import/logic checks pass; GPU path asserts guarded (must run on pod)
- 📁 Files: 4 docs corrected, amd/ restructured (script + 5 artifact slots)
- 🔁 Next prompts: run the script on the AMD pod; commit real artifacts over placeholders
- 🧠 Reflection: checkout moved to main with prior pass already committed (83b3560); single commit on main as instructed
