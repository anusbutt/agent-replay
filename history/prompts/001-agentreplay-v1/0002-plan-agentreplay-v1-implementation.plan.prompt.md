---
id: 0002
title: Plan AgentReplay V1 implementation
stage: plan
date: 2026-07-06
surface: agent
model: claude-fable-5
feature: 001-agentreplay-v1
branch: 001-agentreplay-v1
user: anusbutt
command: /sp.plan
labels: ["plan", "architecture", "fastapi", "sqlmodel", "nextjs", "docker-compose", "replay-engine"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - specs/001-agentreplay-v1/plan.md
 - specs/001-agentreplay-v1/research.md
 - specs/001-agentreplay-v1/data-model.md
 - specs/001-agentreplay-v1/contracts/api.openapi.yaml
 - specs/001-agentreplay-v1/quickstart.md
 - CLAUDE.md (agent context: Active Technologies / Recent Changes appended)
tests:
 - none (planning artifacts; Constitution Check gates G1–G10 evaluated PASS pre- and post-design)
---

## Prompt

/sp.plan (no additional user input)

Execute the implementation planning workflow using the plan template to
generate design artifacts: fill Technical Context, run the Constitution
Check gates, produce Phase 0 research.md, Phase 1 data-model.md, contracts/,
quickstart.md, update agent context, and re-evaluate the Constitution Check
post-design.

## Response snapshot

Generated the full plan set for 001-agentreplay-v1. plan.md: technical
context fully settled (no NEEDS CLARIFICATION — stack pinned in CLAUDE.md),
Constitution Check as 10 explicit gates (principles I–VII, data contract
supremacy, scope guard, fixed stack) — all PASS pre- and post-design;
project structure: app/ (FastAPI backend: models.py, routers per domain,
replay/ engine+interceptor, analysis/ client+serializer+prompts),
sdk/agentreplay/ (buffer/transport/wrapper/tool/state), dashboard/ (Next.js),
root Dockerfile + compose.yml (backend/frontend/db per Principle VII).
research.md: settled decisions recorded (S1–S3) plus seven resolved
implementation decisions — R1 API surface (6 routes), R2 ingest idempotency
(run upsert + per-item step rejection), R3 canonical_json definition
(sort_keys + compact separators + UTF-8 sha256), R4 fork execution loop
(reconstruct → modify → loop model/interceptor with step budget 20),
R5 detection/analysis as strict-JSON LLM-judge on Gemma, R6 fork inference
via REPLAY_BASE_URL (OpenRouter default), R7 postgres:16 compose service +
create_all bootstrap (no migrations in V1). data-model.md: 1:1 transcription
of docs/DATA_CONTRACT.md onto SQLModel entities with validation rules, status
transitions, and verdict shapes. contracts/api.openapi.yaml: OpenAPI 3.1 for
/ingest, /runs, /runs/{id}, /runs/{id}/fork, /runs/{id}/analyze,
/detect/sweep with constitution constraints embedded in descriptions.
quickstart.md: clean checkout → docker compose up → seed → detect → analyze →
fork → side-by-side demo. Agent context script appended Active Technologies
to CLAUDE.md without disturbing curated content.

## Outcome

- ✅ Impact: Complete Phase 0 + Phase 1 design artifacts; feature is ready for /sp.tasks.
- 🧪 Tests: n/a (planning); all 10 constitution gates PASS, Complexity Tracking empty.
- 📁 Files: plan.md, research.md, data-model.md, contracts/api.openapi.yaml, quickstart.md, CLAUDE.md (appended).
- 🔁 Next prompts: /sp.tasks (optionally /sp.adr for the fork-loop/API-surface decision group).
- 🧠 Reflection: With upstream law this settled, planning reduced to bounded implementation decisions (R1–R7) — each traceable to a pinned decision it serves.

## Evaluation notes (flywheel)

- Failure modes observed: update-agent-context.sh appends generated sections to CLAUDE.md; verified no duplication of the curated AgentReplay section before proceeding.
- Graders run and results (PASS/FAIL): PASS — no unresolved placeholders; gates evaluated; artifacts cross-reference each other.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none
