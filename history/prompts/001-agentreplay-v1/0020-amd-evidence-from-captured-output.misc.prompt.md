---
id: 0020
title: AMD evidence from captured output
stage: misc
date: 2026-07-10
surface: agent
model: claude-fable-5
feature: 001-agentreplay-v1
branch: main
user: anusbutt
command: none
labels: ["amd", "rocm", "evidence", "hackathon", "truthfulness"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - amd/environment.txt
 - amd/rocm_smi.txt
 - amd/gpu_compute_check.py
 - amd/gpu_compute_check_output.txt
 - amd/README.md
 - amd/run_analysis_on_amd.py
 - README.md
 - CLAUDE.md
 - .specify/memory/constitution.md
 - specs/001-agentreplay-v1/research.md
tests:
 - py_compile clean on both amd/ scripts
 - repo-wide grep: zero "Gemma 4 26B"/"gemma4"/"26B" and zero executed-on-AMD model claims outside history/prompts/
---

## Prompt

Write the AMD compute evidence artifacts from captured terminal output.
Context: the AMD hackathon pod's gateway is down; the GPU work already ran
successfully and I have the outputs. Commit what is provably true — nothing more.

TASK 1 — Create these files in amd/ (overwrite the placeholders):
[environment.txt, rocm_smi.txt, gpu_compute_check.py,
gpu_compute_check_output.txt — verbatim captures and exact script spec
provided in the prompt, reproduced in the committed files]

TASK 2 — Rewrite amd/README.md. For each file: what it is, what it proves,
how to reproduce. State plainly and without inflation:
- AgentReplay's ROCm/PyTorch stack was brought up on an AMD Radeon gfx1100
  (RDNA3, 48GB) on the AMD Developer Cloud hackathon pod.
- torch.version.hip is populated and torch.version.cuda is None: this is a ROCm
  build, not CUDA. GPU compute was executed and verified.
- The public hosted demo serves root-cause analysis via OpenRouter, which is
  provider-swappable through ANALYSIS_BASE_URL / ANALYSIS_API_KEY / ANALYSIS_MODEL.
  Do not imply the hosted demo runs on AMD.
Add one honest sentence: an on-pod run of the full analysis prompt was prepared
(amd/run_analysis_on_amd.py) but the pod's gateway became unavailable before it
executed; the script is committed and reproducible on any ROCm machine.

TASK 3 — Rewrite the README "AMD Compute Usage" section to match exactly.
DELETE the current claim "Gemma 4 26B loaded onto an AMD Radeon" — that never
happened and is false. Replace with the true claim above. Keep scanner keywords
(ROCm, AMD, gfx1100, Radeon, PyTorch, RDNA3), link to amd/.

TASK 4 — Repo-wide grep outside history/prompts/ for "Gemma 4 26B", "gemma4",
"26B" and any other claim about which model ran on AMD. Remove or correct.
Leave history/prompts/ untouched per CLAUDE.md.

Then: git add -A, commit ("feat(amd): commit AMD compute evidence — ROCm 7.2,
gfx1100, verified GPU compute"), push to main. Show me `git log --oneline -1 main`.

Do not invent any output. If a file needs data I have not given you, stop and ask.

## Response snapshot

Wrote the four evidence files from the user's captured output verbatim
(environment.txt fingerprint; rocm_smi.txt with idle-at-capture header;
gpu_compute_check_output.txt with RDNA3 device-name note).
gpu_compute_check.py reconstructed from the stated spec (ROCm assertions,
device print, seeded 4096x4096 matmul, sync, sum + alloc prints) — flagged
to user that if their original differed the matmul sum won't reproduce.
Deleted the unfulfillable verdict-shaped placeholders (prompt.txt,
verdict.json, verdict.md, rocm_smi_during_inference.txt) since the analysis
run never executed. Rewrote amd/README.md (per-file what/proves/reproduce
table, no inflation, gateway sentence, explicit hosted-demo-not-on-AMD).
Rewrote README "AMD Compute Usage" with the true claims and all scanner
keywords. Corrected residual "executed on AMD" claims in CLAUDE.md,
constitution, research.md, and run_analysis_on_amd.py's docstring
(executed -> prepared). Verified: greps clean, py_compile clean.

## Outcome

- ✅ Impact: every AMD claim in the repo is now backed by a committed artifact or explicitly marked as prepared-but-not-executed
- 🧪 Tests: py_compile clean; claim-grep clean outside verbatim PHRs
- 📁 Files: 4 evidence files written, 4 stale placeholders deleted, 5 docs corrected
- 🔁 Next prompts: if the pod returns, run amd/run_analysis_on_amd.py and commit its artifacts
- 🧠 Reflection: honest "prepared but gateway died" reads far better to judges than an unbackable "it ran"
