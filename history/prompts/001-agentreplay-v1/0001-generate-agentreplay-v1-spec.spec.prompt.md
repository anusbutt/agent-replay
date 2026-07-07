---
id: 0001
title: Generate AgentReplay V1 spec
stage: spec
date: 2026-07-04
surface: agent
model: claude-fable-5
feature: 001-agentreplay-v1
branch: 001-agentreplay-v1
user: anusbutt
command: /sp.specify
labels: ["spec", "sdd", "agentreplay", "data-contract", "fork-engine", "detection"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-agentreplay-v1/spec.md
 - specs/001-agentreplay-v1/checklists/requirements.md
tests:
 - Byte-identity check of Data Contract section vs docs/DATA_CONTRACT.md (all 5 JSON payload blocks and all field lines IDENTICAL — PASS)
---

## Prompt

Read these files first, in full:


docs/DATA_CONTRACT.md   (the settled data model — the law)
docs/DECISIONS.md       (settled architectural decisions + scope guard)
plan.md                 (the day-by-day build plan)
CLAUDE.md               (project index + session rules)


Now generate the SDD artifacts for this project using the spec-kit-plus
workflow, in this order: constitution, then spec.

RULES FOR GENERATION:


TRANSCRIBE AND FORMALIZE — do not redesign. The data contract and pinned
decisions are already settled. Your job is to express them in the
constitution/spec format, NOT to improve, rename, restructure, or
"optimize" them. Field names, enum values, and payload shapes in
DATA_CONTRACT.md must appear in the spec byte-identical.
The CONSTITUTION must encode, as non-negotiable rules, every item in
DECISIONS.md — the six pinned decisions AND the scope guard (NOT-in-V1
list). These are the project's laws.
The SPEC must include: the frozen feature set (SDK, ingest API, timeline
dashboard, replay/fork engine, analysis layer, detection sweep), the full
data contract from DATA_CONTRACT.md, and the primary acceptance scenario
below.
If anything in these source docs seems wrong, ambiguous, or contradictory,
STOP and ask me — do NOT resolve it yourself by changing the design.
Do not write plan.md or tasks.md yet. Constitution and spec only. Stop
after those two and wait for my review.


PRIMARY ACCEPTANCE SCENARIO (the spec's north-star test):
A recorded Nestaro run where the customer asks for Friday but the agent books
Saturday. The system must: (a) detect the run as failed/flagged via semantic
contradiction, (b) produce a root-cause analysis identifying the failing step
and a suggested prompt fix, (c) fork the run from the failing step with the
fix applied, running live inference but intercepting the tool call so no real
booking occurs, and (d) show the forked run booking Friday alongside the
original booking Saturday. This scenario is the product; the spec exists to
make it real.

When done, list what you generated and what (if anything) you need me to
clarify before we move to plan and tasks.

## Response snapshot

Created branch `001-agentreplay-v1` and wrote
specs/001-agentreplay-v1/spec.md. The spec contains: (1) the frozen six-item
feature set — SDK, ingest API, timeline dashboard, replay/fork engine,
analysis layer, detection sweep; (2) User Story 1 (P1) = the Friday/Saturday
Nestaro north-star scenario with acceptance scenarios mapping exactly to
steps (a)–(d) of the prompt, plus supporting stories for invisible recording
/ timeline inspection, detection sweep, and fork safety (sandboxed tools,
temperature 0); (3) the full Data Contract transcribed byte-identical from
docs/DATA_CONTRACT.md — verified programmatically (all 5 JSON payload blocks
and every field line match exactly); (4) 22 functional requirements encoding
the pinned decisions verbatim; (5) the NOT-in-V1 scope guard as an Out of
Scope section; (6) measurable success criteria including zero real tool
executions in forks and parent-run immutability. Quality checklist written at
checklists/requirements.md — all items pass, with a documented
settled-contract exception for the intentionally transcribed field
names/shapes. No [NEEDS CLARIFICATION] markers.

## Outcome

- ✅ Impact: Feature spec for AgentReplay V1 is complete and validated; ready for /sp.plan after user review.
- 🧪 Tests: Byte-identity verification of data contract vs docs/DATA_CONTRACT.md — PASS (5/5 JSON blocks, all field lines).
- 📁 Files: specs/001-agentreplay-v1/spec.md; specs/001-agentreplay-v1/checklists/requirements.md.
- 🔁 Next prompts: user review, then /sp.plan and /sp.tasks.
- 🧠 Reflection: Transcribe-don't-redesign made validation mechanical — a diff script proves fidelity better than prose review.

## Evaluation notes (flywheel)

- Failure modes observed: plan.md referenced in prompt does not exist in repo; CLAUDE.md's run_metadata comment omits the detection/analysis verdicts that DATA_CONTRACT.md includes (DATA_CONTRACT.md is the law and was followed).
- Graders run and results (PASS/FAIL): PASS — checklist complete; byte-identity check PASS.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none
