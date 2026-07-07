---
id: 0010
title: Implement Phase 2 foundational API
stage: green
date: 2026-07-07
surface: agent
model: claude-fable-5
feature: 001-agentreplay-v1
branch: 001-agentreplay-v1
user: anusbutt
command: /sp.implement
labels: ["phase-2", "foundational", "data-contract", "ingest", "runs", "tdd"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - app/models.py
 - app/db.py
 - app/main.py
 - app/schemas.py
 - app/routers/ingest.py
 - app/routers/runs.py
 - tests/conftest.py
 - tests/contract/test_ingest.py
 - tests/contract/test_runs.py
 - scripts/seed_demo_run.py
 - specs/001-agentreplay-v1/tasks.md
 - PROGRESS.md
tests:
 - tests/contract/test_ingest.py (4 tests — verbatim persistence, per-item duplicate rejection, per-item bad-enum rejection, 401)
 - tests/contract/test_runs.py (4 tests — list+filters+lineage fields, seq-ordered detail, 404, 401)
---

## Prompt

phase 1 validated, start phase 2

(Standing maintainer rules from session start: implement phase by phase; stop
after every phase and ask for validation; summarize what was done; list all
files created/updated.)

## Response snapshot

Executed Phase 2 Foundational (T008–T015) in task order with TDD. T008: Run +
Step SQLModel entities mirroring docs/DATA_CONTRACT.md (str-enums persisted by
value, JSONB input/output/run_metadata, UNIQUE (run_id, seq), indexed
agent_id/session_id/run_id, timestamptz columns). T009: db.py engine from
DATABASE_URL + create_all in FastAPI lifespan. T010: static Bearer key
dependency (secrets.compare_digest, env AGENTREPLAY_API_KEY) applied via
include_router; /health open. T011: full schema set per openapi contract;
StepIn deliberately lenient (seq/type validated per-item in handler per R2).
T012: contract tests written FIRST and verified failing (7 failed) against the
running compose db. T013: POST /ingest — run upsert that never downgrades
flagged and never clobbers run_metadata.detection/.analysis, insert-only steps
with per-item rejection (dup seq, bad type, seq<1). T014: GET /runs with
filters + GET /runs/{id} with seq-ordered steps, 404 on unknown. T015:
seed_demo_run.py posts the 5-step Nestaro Friday/Saturday fixture (fixed UUID
1111...-1111, failing llm_call at seq 2 deciding saturday, book_appointment
tool_call saturday, no Authorization key recorded). Verification: 8/8 tests on
host venv AND in-container (docker compose exec backend pytest); backend image
rebuilt; seed accepted=5 and run visible via GET /runs. Commits T-08…T-15.

## Outcome

- ✅ Impact: Foundation complete — a data-contract-conformant run can be ingested, stored, and read back; US1 work unblocked.
- 🧪 Tests: 8/8 contract tests pass (host + container); failing-first verified for TDD gate.
- 📁 Files: 10 source/test files created, main.py extended, tasks.md T008–T015 ticked, PROGRESS.md appended.
- 🔁 Next prompts: maintainer validation → Phase 3 (US1, T016–T031): detection, analysis, fork engine, dashboard, e2e demo.
- 🧠 Reflection: Per-item rejection required lenient StepIn schemas (strict enums would 422 whole batches) — the contract's R2 semantics drove the pydantic design.

## Evaluation notes (flywheel)

- Failure modes observed: compose stack was down at test time (connection refused) — restarted db before the failing-test gate.
- Graders run and results (PASS/FAIL): pytest contract suite PASS (8/8) host and container.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
