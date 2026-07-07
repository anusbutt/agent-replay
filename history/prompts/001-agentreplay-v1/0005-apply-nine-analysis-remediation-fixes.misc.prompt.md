---
id: 0005
title: Apply nine analysis remediation fixes
stage: misc
date: 2026-07-06
surface: agent
model: claude-fable-5
feature: 001-agentreplay-v1
branch: 001-agentreplay-v1
user: anusbutt
command: remediation of /sp.analyze findings (user-approved)
labels: ["remediation", "consistency", "spec", "plan", "tasks", "data-contract-drift"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-agentreplay-v1/spec.md
 - specs/001-agentreplay-v1/plan.md
 - specs/001-agentreplay-v1/tasks.md
 - specs/001-agentreplay-v1/research.md
 - specs/001-agentreplay-v1/data-model.md
 - specs/001-agentreplay-v1/quickstart.md
 - specs/001-agentreplay-v1/contracts/api.openapi.yaml
tests:
 - Task format validation: 50/50 tasks still conform
 - Data-contract byte-identity re-check: field lines PASS; JSON payload blocks FAIL — source docs/DATA_CONTRACT.md was amended externally after transcription (see below)
---

## Prompt

apply all 9 fixes

## Response snapshot

Applied all nine /sp.analyze findings: I1 — ingest upsert protections (never
downgrade flagged, never clobber run_metadata.detection/.analysis) added to
research R2 + T013; U1 — fork identity semantics pinned (copy
agent_id/session_id from parent; fork stores only new steps, seq from 1;
CompareView renders parent prefix) in research R4, data-model.md, T025, T030,
and the fork endpoint description in contracts; U2 — SDK end_run() finalizer
added to T035/T039 API + quickstart snippet + data-model transition note;
I2 — spec pinned to status=flagged for detection (AS-1, US3 AS-1, FR-022,
assumption updated); I3 — invented completed→failed transition removed from
data-model.md; I4 — T005 backend image now includes dev deps + tests/ so
quickstart's `docker compose exec backend pytest` works; U3 — sweep default
candidates exclude forked runs (T040, T042, research R1, contracts
description); I5 — US2 independent test notes API-level verification path;
A1 — plan performance goals given numbers (batch < 500ms, 200-step timeline
< 1s, < 500ms overhead per forked step). DISCOVERED during post-edit
verification: docs/DATA_CONTRACT.md was amended externally since the original
transcription — llm_call.input example now has a history user message +
headers (HTTP-Referer/X-Title), new redaction rule (NEVER record
Authorization), a note that Nestaro sends no tools array (tools are NOT
LLM-native; @replay.tool captures Python functions invoked after text
parsing). This contradicts spec FR-002 wording ("including any tools array,
response_format...") and research R4's fork loop (which assumes model-emitted
tool calls). STOPPED per project law and asked the maintainer before
re-transcribing or redesigning.

## Outcome

- ✅ Impact: All 9 approved fixes landed; artifacts internally consistent — but flagged newly-discovered upstream contract amendment requiring maintainer decisions before /sp.implement.
- 🧪 Tests: format validation 50/50 PASS; contract byte-identity: fields PASS, payload blocks now stale vs amended source (expected — source changed).
- 📁 Files: spec.md, plan.md, tasks.md, research.md, data-model.md, quickstart.md, contracts/api.openapi.yaml.
- 🔁 Next prompts: maintainer answers on (1) re-transcription of amended contract, (2) fork-loop semantics with non-LLM-native tools; then sync pass; then /sp.implement.
- 🧠 Reflection: Re-running the byte-identity check after every edit pass caught an external law change that silent artifact editing would have missed entirely.

## Evaluation notes (flywheel)

- Failure modes observed: source-of-truth document amended mid-workflow without notification; detected only by automated re-verification.
- Graders run and results (PASS/FAIL): fixes PASS; upstream sync check FAIL (expected — awaiting maintainer direction).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): run the byte-identity check at the start of every session touching spec artifacts.
