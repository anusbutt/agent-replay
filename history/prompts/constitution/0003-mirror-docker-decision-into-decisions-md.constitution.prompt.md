---
id: 0003
title: Mirror Docker decision into DECISIONS.md
stage: constitution
date: 2026-07-06
surface: agent
model: claude-fable-5
feature: none
branch: 001-agentreplay-v1
user: anusbutt
command: follow-up to Docker containerization amendment (user consent)
labels: ["constitution", "decisions", "docker", "containerization", "source-of-truth"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - docs/DECISIONS.md
 - .specify/memory/constitution.md
tests:
 - none (documentation artifacts)
---

## Prompt

yes add it there also

## Response snapshot

With maintainer consent, added pinned decision 7 (Docker containerization is
a must-do delivery step) to docs/DECISIONS.md in the doc's existing style:
backend ships as a Docker image from a repo Dockerfile and deploys as that
container; dashboard Dockerfile for local/demo (Vercel remains hosted
target); docker-compose.yml runs the full local stack (backend + dashboard +
Postgres) with one command; env-var-only config, no secrets in images, no
container-specific code paths; SDK not containerized. Updated the
constitution (still v1.1.0 — provenance notes only, no semantic change) to
drop the "pending mirroring" language: Principle VII now transcribes pinned
decision 7, the Sync Impact Report follow-up TODO is cleared, and the intro
states principles transcribe pinned decisions 1–7. Source-of-truth chain is
consistent again: docs/DECISIONS.md → constitution → spec.

## Outcome

- ✅ Impact: Upstream law (docs/DECISIONS.md) and constitution are back in sync; Docker requirement now flows through the full chain of law.
- 🧪 Tests: n/a (documentation artifacts).
- 📁 Files: docs/DECISIONS.md (pinned decision 7 added); .specify/memory/constitution.md (provenance notes updated).
- 🔁 Next prompts: user review complete? then /sp.plan and /sp.tasks.
- 🧠 Reflection: Editing the settled doc only after explicit consent preserved the "transcribe, don't redesign" discipline.

## Evaluation notes (flywheel)

- Failure modes observed: none.
- Graders run and results (PASS/FAIL): PASS — no unresolved placeholders; DECISIONS.md numbering contiguous (1–7); constitution has no remaining "pending" markers.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none
