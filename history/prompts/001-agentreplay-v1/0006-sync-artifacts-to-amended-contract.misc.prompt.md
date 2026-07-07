---
id: 0006
title: Sync artifacts to amended contract
stage: misc
date: 2026-07-06
surface: agent
model: claude-fable-5
feature: 001-agentreplay-v1
branch: 001-agentreplay-v1
user: anusbutt
command: artifact-sync pass (maintainer answers to Q1/Q2)
labels: ["sync", "data-contract", "single-shot-fork", "redaction", "byte-identity"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-agentreplay-v1/spec.md
 - specs/001-agentreplay-v1/data-model.md
 - specs/001-agentreplay-v1/research.md
 - specs/001-agentreplay-v1/plan.md
 - specs/001-agentreplay-v1/tasks.md
 - specs/001-agentreplay-v1/quickstart.md
 - specs/001-agentreplay-v1/contracts/api.openapi.yaml
tests:
 - Byte-identity: 5/5 JSON blocks + 43/43 payload content lines identical in spec.md AND data-model.md; 17/17 field lines in spec.md (data-model uses table form by design)
 - Task format: 50/50 conform
 - Stale-phrase sweep (step budget / fork loop / failed-or-flagged / booking conversation): clean
---

## Prompt

Read docs/DATA_CONTRACT.md, spec.md, data-model.md, research.md, and tasks.md first. I'm answering the two questions you paused on. This is an artifact-sync pass, not implementation — do the full consistent pass, re-run the byte-identity check, then STOP.
Q1 — confirmed intentional. The contract amendment came from Nestaro's real payload. Re-transcribe the payload section byte-identical into spec + data-model. Fix FR-002: drop the "tools array, response_format, extra params" wording (Nestaro sends none). Add a new FR + T037 acceptance for Authorization-header redaction, and add a test asserting a recorded llm_call.input never contains an Authorization key.
Q2 — answer is (b), single-shot fork. Update R4/T025 to this model:

A fork executes exactly ONE live llm_call at the fork step, modification applied to the recorded context, temperature 0. It stores that single new step (seq from 1 per U1).
Do NOT walk subsequent parent steps, do NOT re-issue later llm_calls, do NOT reconstruct Nestaro's "Previous conversation" history format in the engine, do NOT re-execute agent application code (pinned decision #2).
CompareView renders the fork's assistant text against the parent's step-K text AND the parent's subsequent tool_call step(s), with parent steps clearly labeled as parent-origin. The proof is that the model's decision flipped (Saturday → Friday); the fork never re-books anything.
Keep the interceptor/tool-mock machinery (decision #3) in the contract and its isolated tests — it's the generality guarantee for agents that DO emit tool calls (V2/roadmap), just not exercised in the Nestaro single-shot fork path. Add a one-line note so it isn't deleted as unused.

Then run the byte-identity check across spec, data-model, research, tasks, contracts, and report anything that didn't reconcile. STOP before implementation.

## Response snapshot

Full sync pass across seven artifacts. Q1: re-transcribed the amended payload
section (history message in position, headers, Nestaro single-shot notes,
RULES incl. redaction) byte-identical into spec.md and data-model.md; FR-002
rewritten (drops tools-array/response_format wording, names the history
message + HTTP-Referer/X-Title headers); new FR-027 (never record
Authorization; redact at SDK boundary); T033 gains the
no-Authorization-key-in-llm_call.input assertion; T037 acceptance now
requires boundary redaction; T015 seed fixture updated (history message,
headers, no Authorization); SC-002 notes the redaction carve-out. Q2:
research R4 rewritten to single-shot (one live llm_call, single stored step
seq 1, no parent-walking, no history-format reconstruction, no agent code;
CompareView = fork assistant text vs parent step-K text + parent-labeled
tool_calls; proof = flipped decision; interceptor retained as generality
guarantee with keep-note); T018/T025/T030 rewritten to match; T044 reframed
to drive the interceptor directly (not via fork endpoint); US1/US4 phase
goals + spec US1 AS-3/AS-4, US4 story/AS-1, FR-012, FR-015, FR-016 (with
keep-note), FR-016-adjacent edge case, SC-004, new fork-model assumption;
plan.md summary + R4 bullet + engine.py comment updated; quickstart fork and
compare steps updated; contracts fork description updated. Verification:
5/5 JSON blocks and 43/43 payload content lines byte-identical in both spec
and data-model (headings adapted to host doc level — content identical);
17/17 field lines in spec (data-model uses table form by design); 50/50 task
format; stale-phrase sweep clean (remaining "tools array"/"agentic loop"
mentions are transcribed contract text or alternatives-considered prose).
Everything reconciled. STOPPED before implementation as instructed.

## Outcome

- ✅ Impact: All artifacts consistent with the amended data contract and the settled single-shot fork model; ready for /sp.implement.
- 🧪 Tests: byte-identity RECONCILED (5/5 blocks, 43/43 lines, both docs); task format 50/50; stale sweep clean.
- 📁 Files: spec.md, data-model.md, research.md, plan.md, tasks.md, quickstart.md, contracts/api.openapi.yaml.
- 🔁 Next prompts: /sp.implement starting at T001 (one task per session).
- 🧠 Reflection: The single-shot decision simplified the engine and decoupled it from Nestaro's prompt conventions; the interceptor keep-note prevents a future session from "cleaning up" constitutionally mandated machinery.

## Evaluation notes (flywheel)

- Failure modes observed: heading-level differences between contract and host docs initially read as missing lines; resolved by comparing heading content, not markers.
- Graders run and results (PASS/FAIL): PASS — RECONCILED verdict from the automated check; no unresolved contradictions.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none
