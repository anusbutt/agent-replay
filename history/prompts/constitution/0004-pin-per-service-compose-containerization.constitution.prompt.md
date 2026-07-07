---
id: 0004
title: Pin per-service compose containerization
stage: constitution
date: 2026-07-06
surface: agent
model: claude-fable-5
feature: none
branch: 001-agentreplay-v1
user: anusbutt
command: scope confirmation for Docker containerization (pinned decision 7)
labels: ["constitution", "decisions", "docker", "compose", "containerization"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - docs/DECISIONS.md
 - .specify/memory/constitution.md
 - specs/001-agentreplay-v1/spec.md
tests:
 - none (documentation artifacts)
---

## Prompt

keep the full stack containeration. with compose.yml file not a monster image. so "docker compose up" commmand wired up all three: backend, frontend and db

## Response snapshot

Maintainer confirmed the full-stack containerization scope and sharpened it:
one image/container per service — backend (FastAPI), frontend (dashboard),
db (Postgres) — NEVER a single combined "monster" image, and `docker compose
up` wires up all three from the repo's compose file. Updated all three layers
of law to state this explicitly: docs/DECISIONS.md pinned decision 7,
constitution Principle VII (v1.1.0 — wording sharpened, no semantic version
change), and the spec (FR-024 "its own Dockerfile", FR-025 three separate
services / never a single combined image, SC-008 names `docker compose up`
against three separate containers, Assumptions entry marked confirmed by
maintainer instead of pending).

## Outcome

- ✅ Impact: Containerization architecture is now unambiguous across the chain of law — per-service images composed by `docker compose up`, no monolith image.
- 🧪 Tests: n/a (documentation artifacts).
- 📁 Files: docs/DECISIONS.md; .specify/memory/constitution.md; specs/001-agentreplay-v1/spec.md.
- 🔁 Next prompts: /sp.plan then /sp.tasks (constitution + spec review complete).
- 🧠 Reflection: The earlier open question resolved exactly onto the recommended default, with the useful addition of the explicit anti-monolith rule.

## Evaluation notes (flywheel)

- Failure modes observed: none.
- Graders run and results (PASS/FAIL): PASS — DECISIONS.md, constitution, and spec all state the same three-service compose rule; no unresolved placeholders.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none
