---
id: 0018
title: AMD compute evidence and claim scrub
stage: misc
date: 2026-07-10
surface: agent
model: claude-fable-5
feature: 001-agentreplay-v1
branch: 001-agentreplay-v1
user: anusbutt
command: none
labels: ["amd", "hackathon", "docs", "compliance"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - CLAUDE.md
 - README.md
 - PROGRESS.md
 - .env.example
 - .specify/memory/constitution.md
 - app/analysis/client.py
 - specs/001-agentreplay-v1/plan.md
 - specs/001-agentreplay-v1/quickstart.md
 - specs/001-agentreplay-v1/research.md
 - specs/001-agentreplay-v1/tasks.md
 - amd/README.md
 - amd/run_gemma_analysis.py
 - amd/analysis_prompt.txt
 - amd/gemma4_verdict_on_amd.json
 - amd/rocm_smi_during_inference.txt
tests:
 - repo-wide grep: zero remaining MI300/Instinct/AMD-hardware-hosted/Radeon PRO mentions outside verbatim PHR records
---

## Prompt

Read CLAUDE.md, README.md, docs/DECISIONS.md, docs/DATA_CONTRACT.md, spec.md, plan.md.
Critical context: the hackathon guide states that for Track 3, "AMD compute usage is a requirement: projects that do not demonstrate it will be disqualified," and that "automated pre-screening only inspects the GitHub repository, slide deck (PDF), and live demo/hosted URL — it does not process the demo video." So evidence of AMD compute must live in the repository, in text a scanner can read. Video footage does not count.
Do these three things, then STOP:

Scrub false hardware claims. Remove or correct every mention of MI300X, AMD Instinct, or Fireworks-as-AMD-host anywhere in the repo. The truth: analysis inference for the public demo runs Gemma 4 via OpenRouter; a separate documented run executed Gemma 4 26B on an AMD Radeon (gfx1100) GPU via ROCm on the hackathon's AMD compute pod. Do not write any claim we cannot back with a committed artifact.
Create an amd/ directory with a README.md explaining what will live there: the script that ran Gemma 4 on AMD hardware via ROCm, the real analysis prompt used, the verdict Gemma 4 produced, and captured rocm-smi output showing the gfx1100 device and VRAM occupied. Leave placeholders for run_gemma_analysis.py, analysis_prompt.txt, gemma4_verdict_on_amd.json, rocm_smi_during_inference.txt — I will supply the real files.
Add an "AMD Compute Usage" section to the main README, near the top, stating plainly that Gemma 4 26B was loaded onto an AMD Radeon (gfx1100) GPU via ROCm (torch+rocm) on the AMD compute pod provided by the hackathon, where it produced AgentReplay's root-cause analysis verdict, and linking to amd/. Write it so both a human judge and an automated scanner find it: include the words ROCm, AMD, gfx1100, Gemma 4.

## Response snapshot

Scrubbed every MI300X/Instinct/Fireworks-as-AMD-host claim from live docs
(CLAUDE.md, README, constitution, plan, research, quickstart, tasks,
.env.example, PROGRESS.md, client.py docstrings); canonical truth is now:
public demo analysis = Gemma 4 via OpenRouter (provider swap =
ANALYSIS_BASE_URL/API_KEY/MODEL env vars); AMD compute demonstrated
separately in amd/. Created amd/ with README describing the four evidence
artifacts and clearly-marked placeholders (run_gemma_analysis.py,
analysis_prompt.txt, gemma4_verdict_on_amd.json,
rocm_smi_during_inference.txt) pending the real captured files. Added
"AMD Compute Usage" section near the top of README.md containing ROCm,
AMD, gfx1100, Gemma 4 keywords and linking to amd/. Verbatim PHR records
under history/prompts/ left untouched by design.

## Outcome

- ✅ Impact: repo makes only backable claims; scanner-readable AMD evidence path established
- 🧪 Tests: repo-wide grep clean (0 hits outside verbatim PHRs); no code behavior changed beyond docstrings
- 📁 Files: 10 scrubbed, 5 created under amd/
- 🔁 Next prompts: user supplies the four real artifacts; commit + push before submission
- 🧠 Reflection: placeholders are explicitly labeled so no one can mistake scaffolding for evidence

## Evaluation notes (flywheel)

- none
