---
id: 0001
title: Ratify AgentReplay constitution v1
stage: constitution
date: 2026-07-04
surface: agent
model: claude-fable-5
feature: none
branch: 001-agentreplay-v1
user: anusbutt
command: /sp.constitution
labels: ["constitution", "sdd", "agentreplay", "pinned-decisions", "scope-guard"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - .specify/memory/constitution.md
tests:
 - none (documentation artifact; validated against docs/DECISIONS.md and docs/DATA_CONTRACT.md)
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

Ratified `.specify/memory/constitution.md` v1.0.0 for AgentReplay. The six
pinned decisions from docs/DECISIONS.md were transcribed 1:1 as Core
Principles I–VI: (I) fork = new run, parent immutability; (II)
conversation-level replay, not program-level; (III) tool interception order
(positional → sha256 fallback → typed mock, never a real tool); (IV) forked
LLM calls at temperature 0 unless overridden; (V) SDK never raises into host
code; (VI) verdicts stored under run_metadata.detection / run_metadata.analysis.
Added a Data Contract Supremacy section binding docs/DATA_CONTRACT.md as law,
the verbatim NOT-in-V1 scope guard, workflow/session rules, and governance
(amendments flow from source docs first; semver policy; mandatory Constitution
Check for plans/tasks). No redesign, no renames. Note: plan.md referenced in
the prompt does not exist in the repo — flagged to user, not blocking for
constitution/spec.

## Outcome

- ✅ Impact: Project constitution ratified at v1.0.0; all six pinned decisions and the scope guard are now enforceable law for planning and implementation.
- 🧪 Tests: n/a (documentation artifact); transcription cross-checked against docs/DECISIONS.md.
- 📁 Files: .specify/memory/constitution.md (overwritten from template).
- 🔁 Next prompts: /sp.plan and /sp.tasks after user reviews constitution + spec.
- 🧠 Reflection: Template's six principle slots mapped exactly onto the six pinned decisions; transcription (not synthesis) kept fidelity trivially verifiable.

## Evaluation notes (flywheel)

- Failure modes observed: referenced plan.md missing from repo; proceeded (not needed for these artifacts) and flagged.
- Graders run and results (PASS/FAIL): PASS — all DECISIONS.md items present in constitution; no placeholder tokens remain.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none
