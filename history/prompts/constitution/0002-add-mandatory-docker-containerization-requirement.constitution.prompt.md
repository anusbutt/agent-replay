---
id: 0002
title: Add mandatory Docker containerization requirement
stage: constitution
date: 2026-07-06
surface: agent
model: claude-fable-5
feature: none
branch: 001-agentreplay-v1
user: anusbutt
command: constitution + spec amendment (user request)
labels: ["constitution", "spec", "docker", "containerization", "amendment"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - .specify/memory/constitution.md
 - specs/001-agentreplay-v1/spec.md
 - specs/001-agentreplay-v1/checklists/requirements.md
tests:
 - none (documentation artifacts)
---

## Prompt

i forgot a mandatory thing that is docker containerization. it's a must do step. add this in constitution and spec first

## Response snapshot

Amended the constitution to v1.1.0 (MINOR bump) adding Principle VII: Docker
Containerization (MANDATORY): backend ships as a Docker image built from a
repo Dockerfile and runs as that container in deployment; dashboard gets a
Dockerfile for local/demo use (Vercel remains the hosted target);
docker-compose.yml brings up the full local stack (backend + dashboard +
Postgres) with one command; env-var-only configuration, no secrets in images,
no container-specific code paths; the SDK (embedded library) is not
containerized. Governance Constitution Check now covers I–VII. Spec updated
with FR-023–FR-026 (Docker containerization requirement group), SC-008
(single command brings up containerized stack from clean checkout and the
primary acceptance scenario passes against it), and an Assumptions entry
recording the scope choice. Checklist updated with a documented Docker
exception (technology named because it IS the requirement). Asked the user to
confirm containerization scope (full-stack compose vs backend-only); no
response after 60s, proceeded with the recommended full-stack-compose scope,
flagged as pending confirmation. Follow-up TODO recorded: mirror Principle
VII into docs/DECISIONS.md as pinned decision 7 (maintainer edit) to keep the
upstream law consistent.

## Outcome

- ✅ Impact: Docker containerization is now constitutional law (Principle VII) and spec'd as FR-023–FR-026 / SC-008 before plan and tasks are generated.
- 🧪 Tests: n/a (documentation artifacts).
- 📁 Files: .specify/memory/constitution.md (v1.1.0); specs/001-agentreplay-v1/spec.md; specs/001-agentreplay-v1/checklists/requirements.md.
- 🔁 Next prompts: confirm Docker scope choice; mirror into docs/DECISIONS.md; then /sp.plan.
- 🧠 Reflection: New law arriving outside docs/DECISIONS.md creates a source-of-truth gap; recorded a TODO to mirror it upstream rather than silently editing the settled doc.

## Evaluation notes (flywheel)

- Failure modes observed: scope of "containerization" was ambiguous (backend-only vs full stack); user unavailable to answer, so recommended default applied and flagged.
- Graders run and results (PASS/FAIL): PASS — no unresolved placeholders; constitution version/dates consistent; spec FR numbering contiguous.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none
