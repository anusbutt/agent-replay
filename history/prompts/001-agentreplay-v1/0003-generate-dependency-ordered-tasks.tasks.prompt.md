---
id: 0003
title: Generate dependency-ordered tasks
stage: tasks
date: 2026-07-06
surface: agent
model: claude-fable-5
feature: 001-agentreplay-v1
branch: 001-agentreplay-v1
user: anusbutt
command: /sp.tasks
labels: ["tasks", "planning", "user-stories", "tdd", "docker-compose", "mvp"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-agentreplay-v1/tasks.md
tests:
 - none (planning artifact); format validation: 50/50 tasks match the required checklist format, 0 violations
---

## Prompt

/sp.tasks (no additional user input)

Generate an actionable, dependency-ordered tasks.md for the feature based on
available design artifacts (plan.md, spec.md, research.md, data-model.md,
contracts/api.openapi.yaml, quickstart.md), organized by user story with
strict checklist format, dependency graph, parallel examples, and
implementation strategy.

## Response snapshot

Generated specs/001-agentreplay-v1/tasks.md with 50 tasks across 7 phases.
Phase 1 Setup (T001–T007): scaffolding, backend/dashboard init, .env.example,
backend + frontend Dockerfiles, compose.yml with exactly three services
(constitution VII gate at the checkpoint). Phase 2 Foundational (T008–T015):
SQLModel entities mirroring the data contract, db bootstrap, static-key auth,
schemas, contract tests, POST /ingest (idempotent per research R2), GET
/runs(+detail), Friday/Saturday seed script — blocking for all stories since
every independent test needs a stored run. Phase 3 US1/P1 MVP (T016–T031, 16
tasks): failing-first integration tests for detection/analysis/fork, analysis
client/serializer/prompts, detection + analysis endpoints, interceptor
(canonical_json + 3-tier resolution), replay engine (reconstruct → modify →
temp-0 loop → 20-step budget), fork endpoint, dashboard (api client, runs
list, timeline + verdicts, fork panel + side-by-side compare), and T031 = the
live end-to-end demo gate (SC-001). Phase 4 US2/P2 (T032–T039, 8 tasks): SDK
unit/integration tests (buffer, verbatim wrapper, never-raises), package
skeleton, buffer/transport, wrap(), @tool + state_change, demo agent script
proving invisibility. Phase 5 US3/P3 (T040–T042): selective-sweep test,
correct/running fixtures, sweep hardening. Phase 6 US4/P3 (T043–T046):
canonical_json vectors, interception-tier tests with real-tool spy,
temperature/immutability tests, engine hardening. Phase 7 Polish (T047–T050):
ROADMAP.md for scope-guard items, README, clean-checkout SC-008 validation,
final constitution sweep. Tests included (constitution makes tests the
contract's enforcement mechanism) and written before implementation; tests/
files created only by dedicated test tasks, honoring the never-edit-tests
session rule. Dependency graph: US1 depends only on Foundational (seeded
fixture, no SDK); US3 depends on US1's detection core; US4 on US1's fork
engine. Parallel markers on 20 tasks; MVP = Phases 1–3.

## Outcome

- ✅ Impact: Executable task list ready for /sp.implement — one task per session, each with acceptance criteria and exact paths.
- 🧪 Tests: n/a (planning); format validation 50/50 pass.
- 📁 Files: specs/001-agentreplay-v1/tasks.md.
- 🔁 Next prompts: /sp.implement (T001 first) or /sp.analyze for cross-artifact consistency check.
- 🧠 Reflection: US1-first ordering works only because Foundational includes ingest + seed fixture — the spec's "seeded run is acceptable" assumption is what makes the MVP independent of the SDK.

## Evaluation notes (flywheel)

- Failure modes observed: strict story independence impossible (US1 subsumes detection/fork); resolved by scoping US3/US4 to breadth/safety-proof tasks and declaring explicit story dependencies instead of pretending independence.
- Graders run and results (PASS/FAIL): PASS — 50 tasks all match `- [ ] TNNN [P?] [USn?] description + path` format (grep-validated, 0 violations).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none
