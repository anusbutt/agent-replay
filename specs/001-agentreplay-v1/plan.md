# Implementation Plan: AgentReplay V1

**Branch**: `001-agentreplay-v1` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-agentreplay-v1/spec.md`

## Summary

AgentReplay V1 is a flight recorder and time-travel debugger for AI agents: a
Python SDK records every step (llm_call, tool_call, state_change) of a host
agent verbatim and ships them fire-and-forget to a FastAPI ingest API backed
by Postgres; a Next.js dashboard renders run timelines; a replay engine forks
a run from any step with a modification, executing a single live LLM call at
temperature 0 (research R4 single-shot; tool-interception machinery —
positional → hash → typed mock, never real — guards any tool-emitting
replay); an analysis layer (Gemma 4 on vLLM/MI300X, OpenAI-compatible)
produces detection and root-cause verdicts stored on `run_metadata`. The
north-star acceptance path is the Nestaro Friday/Saturday scenario: detect →
analyze → fork with fix → side-by-side comparison. Delivery is containerized:
three compose services (backend, frontend, db) wired by `docker compose up`.

## Technical Context

**Language/Version**: Python 3.11+ (SDK + backend); TypeScript (dashboard)
**Primary Dependencies**: SDK: httpx (async, batched, fire-and-forget).
Backend: FastAPI + SQLModel. Dashboard: Next.js + Tailwind (no other UI
libs). Analysis/detection inference: Gemma 4 served by vLLM on AMD MI300X (AMD
Developer Cloud), OpenAI-compatible endpoint; fallback same Gemma 4 family via
Fireworks API; switch = `ANALYSIS_BASE_URL` env var only. Forbidden: LangChain,
LangGraph, ORMs other than SQLModel, message queues.
**Storage**: Postgres — NeonDB hosted; local Postgres container under compose.
Fixed columns for structure, JSONB for payloads (per docs/DATA_CONTRACT.md).
**Testing**: pytest (backend + SDK); acceptance via curl/scripted checks per
task. `tests/` is read-only law for implementation sessions.
**Target Platform**: Backend container on Railway; dashboard on Vercel
(hosted) and container (local/demo); full local stack via `docker compose up`
(backend, frontend, db).
**Project Type**: Web application (backend + frontend) + standalone SDK package.
**Performance Goals**: Demo-grade: ingest keeps up with a single interactive
agent conversation in real time (batch persisted < 500ms locally); timeline
loads a full run (≤ 200 steps) in one request in < 1s on the local compose
stack; fork round-trip bounded by live model latency, not by AgentReplay
overhead (< 500ms added per forked step).
**Constraints**: SDK must never raise into host code (pinned decision 5);
verbatim payload storage (no summarize/trim); forked runs execute zero real
tools; single static API key; scope guard (NOT-in-V1 list) is law.
**Scale/Scope**: Hackathon V1 (AMD Developer Hackathon ACT II, Jul 6–11,
2026), solo builder, one demo agent (Nestaro), tens of runs, hundreds of steps.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Principle / Rule | Plan compliance | Status |
|------|------------------|-----------------|--------|
| G1 | I. Fork = new run; parent immutability | Fork endpoint creates a new `runs` row with `parent_run_id` + `fork_step`; no UPDATE path touches parent steps; replay engine reads parent steps read-only | PASS |
| G2 | II. Conversation-level replay | Replay engine reconstructs recorded `llm_call.input` at fork step, applies modification, calls model live; no import/execution of host agent code | PASS |
| G3 | III. Tool interception order; never real tools | `ToolInterceptor` resolves: (run_id, seq) positional → sha256(name + canonical_json(args)) → typed mock `{"result": {"mocked": true}, "error": null}`; fork path has no code route to real tool execution | PASS |
| G4 | IV. Fork temperature 0 unless overridden | Fork request model has optional `temperature`; engine defaults to 0 | PASS |
| G5 | V. SDK never raises into host code | All SDK I/O wrapped in try/except; errors logged to local logger only; flush is fire-and-forget | PASS |
| G6 | VI. Verdicts on `run_metadata.detection` / `.analysis` | Detection + analysis writers merge JSONB keys into `run_metadata`; no new tables | PASS |
| G7 | VII. Docker: per-service containers, `docker compose up` wires backend + frontend + db; never a monster image | Root `Dockerfile` (backend), `dashboard/Dockerfile` (frontend), root `compose.yml` with three services; env-var-only config | PASS |
| G8 | Data Contract Supremacy | `app/models.py` mirrors docs/DATA_CONTRACT.md field-for-field; ingest validates payload shapes; tests assert them | PASS |
| G9 | Scope Guard (NOT-in-V1) | No auth beyond static key, no multi-tenant UI, no rate limiting, no OTel, no framework integrations, no streaming ingestion, no one-click deploy anywhere in this plan | PASS |
| G10 | Fixed stack | FastAPI/SQLModel/NeonDB/Next.js/Tailwind/httpx/vLLM-Gemma 4 exactly as pinned; nothing substituted | PASS |

**Initial gate result: PASS (no violations, Complexity Tracking empty).**
**Post-design re-check (after Phase 1): PASS — data-model.md is a 1:1
transcription of the data contract; contracts/ expose no out-of-scope
surface; quickstart uses `docker compose up`.**

## Project Structure

### Documentation (this feature)

```text
specs/001-agentreplay-v1/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/
│   └── api.openapi.yaml # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
app/                         # FastAPI backend (compose service: backend)
├── main.py                  # app factory, router mounting, static-key dependency
├── db.py                    # engine/session from DATABASE_URL
├── models.py                # SQLModel: Run, Step (mirrors docs/DATA_CONTRACT.md)
├── schemas.py               # pydantic request/response bodies (ingest batch, fork, verdicts)
├── routers/
│   ├── ingest.py            # POST /ingest
│   ├── runs.py              # GET /runs, GET /runs/{run_id}
│   ├── fork.py              # POST /runs/{run_id}/fork
│   ├── analysis.py          # POST /runs/{run_id}/analyze
│   └── detection.py         # POST /detect/sweep
├── replay/
│   ├── engine.py            # context reconstruction + single-shot fork (one live llm_call, temp 0)
│   └── interceptor.py       # positional → hash → typed-mock tool resolution
└── analysis/
    ├── client.py            # OpenAI-compatible client on ANALYSIS_BASE_URL
    ├── serializer.py        # run → analysis-prompt serialization
    └── prompts.py           # detection + root-cause prompt templates

sdk/agentreplay/             # Python SDK (own package; NOT containerized)
├── __init__.py              # replay.init / public API
├── wrapper.py               # replay.wrap(client) — records llm_call verbatim
├── tool.py                  # @replay.tool decorator — records tool_call
├── state.py                 # record_state_change()
├── buffer.py                # in-memory buffer, batched flush
└── transport.py             # httpx fire-and-forget; swallow + log all errors

dashboard/                   # Next.js + Tailwind (compose service: frontend)
├── Dockerfile
└── src/
    ├── app/
    │   ├── page.tsx                 # runs list
    │   └── runs/[id]/page.tsx       # timeline + verdicts + fork UI + side-by-side compare
    ├── components/                  # TimelineStep, VerdictBadge, ForkPanel, CompareView
    └── lib/api.ts                   # typed fetchers for backend API

tests/                       # read-only during implementation sessions
├── contract/                # ingest validation, data-contract assertions
├── integration/             # fork engine, interception, detection/analysis flows
└── unit/                    # SDK buffer/wrapper, canonical_json, hashing

Dockerfile                   # backend image (compose service: backend; Railway deploy artifact)
compose.yml                  # wires backend + frontend + db (one container per service)
.env.example                 # DATABASE_URL, AGENTREPLAY_API_KEY, ANALYSIS_BASE_URL, ANALYSIS_API_KEY, REPLAY_BASE_URL, REPLAY_API_KEY
```

**Structure Decision**: Web application layout with a separate SDK package.
Backend lives in `app/` with SQLModel models in `app/models.py` and routers
per domain in `app/routers/` (CLAUDE.md conventions). SDK is its own package
dir `sdk/agentreplay/`. Dashboard is `dashboard/`, exposed as compose service
`frontend`. Three container services (backend, frontend, db) per constitution
Principle VII; the SDK ships as a library, not a container.

## Architecture Decisions (this plan)

Settled upstream (constitution I–VII) and NOT re-decided here: fork model,
replay level, interception order, temperature policy, SDK error swallowing,
verdict storage, containerization shape. The plan adds the following
implementation-level decisions, detailed in [research.md](./research.md):

- **API surface** (R1): five REST endpoints — `POST /ingest`, `GET /runs`,
  `GET /runs/{run_id}`, `POST /runs/{run_id}/fork`, `POST
  /runs/{run_id}/analyze`, `POST /detect/sweep` — all under a single static
  key (`Authorization: Bearer $AGENTREPLAY_API_KEY`).
- **Ingest idempotency** (R2): run row upserted from first event; step insert
  relies on UNIQUE (run_id, seq); duplicates rejected per-item without
  failing the batch.
- **canonical_json** (R3): JSON with sorted keys, no insignificant
  whitespace (`separators=(",", ":")`), UTF-8; hash = sha256 of
  `name + canonical_json(args)`.
- **Single-shot fork** (R4, settled by maintainer 2026-07-06): exactly ONE
  live llm_call at the fork step from the reconstructed, modified context;
  the fork stores that single step (seq 1). No walking of subsequent parent
  steps, no history-format reconstruction, no agent code re-execution.
  Interceptor machinery retained as the guarantee for tool-emitting agents
  (not exercised by Nestaro's single-shot path).
- **Detection & analysis as LLM-judge** (R5): serialized run sent to the
  Gemma 4 endpoint with structured-JSON verdict prompts; verdict merged into
  `run_metadata` and status set to `flagged` on detection failure.
- **Fork inference endpoint** (R6): OpenAI-compatible client configured by
  `REPLAY_BASE_URL`/`REPLAY_API_KEY` (defaults to OpenRouter, matching
  recorded model ids).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

None — all gates pass; no deviations to justify.
