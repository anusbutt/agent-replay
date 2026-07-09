<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0 (MINOR: new principle added)
- Modified principles: none renamed/removed
- Added sections:
  - Principle VII: Docker Containerization (MANDATORY) — added 2026-07-06 by
    maintainer decree; mirrored into docs/DECISIONS.md as pinned decision 7
    on 2026-07-06 with maintainer consent
- Removed sections: none
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md (Constitution Check section is generic; compatible as-is)
  - ✅ .specify/templates/spec-template.md (no constitution-specific tokens; compatible as-is)
  - ✅ .specify/templates/tasks-template.md (no constitution-specific tokens; compatible as-is)
- Follow-up TODOs: none.
- Source of law: docs/DECISIONS.md and docs/DATA_CONTRACT.md — this file transcribes,
  it does not redesign. If this file and those docs ever disagree, STOP and reconcile;
  do not silently pick one.

Prior version (1.0.0, ratified 2026-07-04):
- Initial ratification — Core Principles I–VI transcribed 1:1 from
  docs/DECISIONS.md pinned decisions; Scope Guard — NOT in V1; Data Contract
  Supremacy; Development Workflow & Session Rules; Governance.
-->

# AgentReplay Constitution

AgentReplay is a flight recorder and time-travel debugger for AI agents: a Python
SDK records every step of an agent's execution; a FastAPI backend ingests and
persists runs; a Next.js dashboard renders timelines; a replay engine forks runs
from any step with modifications under sandboxed tool calls; an analysis layer
produces detection and root-cause verdicts. Built solo for the AMD Developer
Hackathon ACT II (Jul 6–11, 2026). Demo agent: Nestaro.

The principles below transcribe the settled decisions in `docs/DECISIONS.md`
(pinned decisions 1–7) and the data model in `docs/DATA_CONTRACT.md`. They
are non-negotiable. Do not
re-decide them inside a session. If a task appears to require contradicting one,
STOP and ask — those source documents are the tiebreaker.

## Core Principles

### I. Fork = New Run (Parent Immutability)
A fork is a new row in `runs` with `parent_run_id` and `fork_step` set. The
parent run and its steps are NEVER modified. Any implementation, migration, or
"optimization" that mutates a parent run or its steps violates this constitution.

### II. Conversation-Level Replay, Not Program-Level
Replay reconstructs the recorded `llm_call.input` at the fork step, applies the
user's modification, and calls the model live from there. We do NOT re-execute
the agent's application code. No feature may require importing, invoking, or
re-running the host agent's program logic to perform a replay.

### III. Tool Interception During Forks (NON-NEGOTIABLE)
During a fork, tool calls are intercepted and resolved in this exact order:
1. Match a cached result by (run_id, seq) positionally;
2. Fallback match by sha256(name + canonical_json(args));
3. No match → return typed mock `{"result": {"mocked": true}, "error": null}`.

A forked run NEVER executes a real tool. No exceptions, no side effects.

### IV. Deterministic Forked Inference
Forked LLM calls run at temperature 0 unless the fork request explicitly
overrides. Replay tests fidelity of context, not model chance.

### V. SDK Invisibility (Never Raise Into Host Code)
The SDK must never raise into host agent code. All transport/recording errors
are swallowed and logged locally. A recording failure must be invisible to the
agent it records.

### VI. Verdicts Live on Run Metadata
Detection and analysis results are stored as JSONB on the run's metadata under
`run_metadata.detection` and `run_metadata.analysis`. No separate verdict
tables, no alternative storage locations.

### VII. Docker Containerization (MANDATORY)
Docker containerization is a must-do delivery step, not an optional nicety.
Full-stack containerization via compose — one container per service, NEVER a
single combined "monster" image.
- The stack is three services, each its own image/container: backend
  (FastAPI: ingest API + replay/fork engine + analysis/detection), frontend
  (dashboard), and db (Postgres).
- `docker compose up` from the repo's compose file MUST wire up all three.
- The backend MUST ship as a Docker image built from a Dockerfile in the
  repo, and the deployed backend MUST run as that container.
- The frontend MUST have its own Dockerfile so it can run as a container for
  local/demo use (Vercel remains the hosted deploy target).
- Containers are configured via environment variables only (`.env`); no
  secrets baked into images; no container-specific code paths — behavior
  inside a container is identical to behavior outside it.
The SDK is a Python library embedded in host agents; it is not containerized.

## Data Contract Supremacy

`docs/DATA_CONTRACT.md` is the law. Every component obeys it: the SDK writes it,
ingest validates it, the timeline renders it, the fork engine reads it, the
tests assert it. Its rules, binding here:

- Table `runs`: `id` (UUID pk), `agent_id` (str, indexed), `session_id` (str,
  indexed), `status` enum(running, completed, failed, flagged), `parent_run_id`
  (UUID fk → runs.id, nullable, set only on forks), `fork_step` (int, nullable),
  `run_metadata` (JSONB), `started_at`/`ended_at` (timestamptz).
- Table `steps`: `id` (UUID pk), `run_id` (UUID fk → runs.id, indexed), `seq`
  (int, 1-based per run, UNIQUE on (run_id, seq)), `type` enum(llm_call,
  tool_call, state_change), `input` (JSONB), `output` (JSONB), `latency_ms`
  (int, nullable), `tokens_in`/`tokens_out` (int, nullable, llm_call only),
  `created_at` (timestamptz).
- Payloads are recorded VERBATIM — never summarize, never trim. Record LLM
  requests EXACTLY as sent (including any tools array, response_format, or
  extra params) and responses EXACTLY as received.
- No component may add, rename, or drop fields without updating
  `docs/DATA_CONTRACT.md` first, and any such change requires a constitution
  amendment (see Governance).

## Scope Guard — NOT in V1

Do not build, scaffold, or "prepare for" any of these. If a task seems to need
one, STOP and say so instead of building it:

- Auth beyond a single static API key
- Multi-tenant UI
- Rate limiting
- OpenTelemetry / OTel compatibility
- Framework integrations (LangChain, LangGraph, etc.)
- Streaming ingestion
- One-click deploy of a fix to a live agent (fixes are copied manually — the
  human gate on irreversible action is deliberate, not a missing feature)

Every item above is a real roadmap entry and a wrong hackathon entry. They go
in ROADMAP.md, never in code.

## Development Workflow & Session Rules

- Stack is fixed (do not substitute): Python 3.11+ SDK with httpx; FastAPI +
  SQLModel backend; NeonDB (Postgres) with fixed columns for structure and
  JSONB for payloads; Next.js + TypeScript dashboard with Tailwind only;
  analysis inference via Gemma 4 on OpenRouter (AMD-hardware-hosted
  inference via Fireworks AI is the intended production target once
  deployed), switched by `ANALYSIS_BASE_URL` env var only. No LangChain, no LangGraph, no
  ORMs other than SQLModel, no message queues.
- One task from tasks.md per session; done = the task's acceptance criteria
  pass, verified by actually running them (pytest / curl / stated check).
- Never modify files under `tests/`. If a test seems wrong, stop and report.
- Commits: small, per task, message format "T-NN: <what>".
- Type hints everywhere; pydantic models for all API request/response bodies.
- No hardcoded secrets or tokens; use `.env`.

## Governance

- This constitution supersedes all other practices. When it conflicts with any
  code, plan, task, or convenience, the constitution wins — or the work stops
  until the conflict is resolved with the maintainer.
- The source documents `docs/DECISIONS.md` and `docs/DATA_CONTRACT.md` are the
  upstream law. Amending a principle here requires first amending the source
  document, then updating this file to match, with a version bump.
- Versioning policy: MAJOR for removing/redefining a principle or changing the
  data contract incompatibly; MINOR for adding a principle or materially new
  guidance; PATCH for clarifications and wording.
- All plans and task lists MUST pass a Constitution Check against Principles
  I–VII and the Scope Guard before implementation begins. Any violation is a
  blocker, not a judgment call.
- Uncertainty rule: if uncertain about replay/fork semantics or the data
  contract, stop and ask. Do not guess.

**Version**: 1.1.0 | **Ratified**: 2026-07-04 | **Last Amended**: 2026-07-06
