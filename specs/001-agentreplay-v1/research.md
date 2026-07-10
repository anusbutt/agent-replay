# Phase 0 Research: AgentReplay V1

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-07-06

No `NEEDS CLARIFICATION` markers exist in the Technical Context — the stack,
data model, and core semantics are settled law (docs/DATA_CONTRACT.md,
docs/DECISIONS.md, constitution v1.1.0). This document (a) records those
settled choices with their rationale for traceability, and (b) resolves the
implementation-level unknowns the settled docs intentionally leave open.

## Settled upstream (recorded, not re-decided)

### S1. Stack

- **Decision**: SDK: Python 3.11+ + httpx. Backend: FastAPI + SQLModel.
  DB: NeonDB Postgres (fixed columns + JSONB payloads). Dashboard: Next.js +
  TypeScript + Tailwind, shadcn/ui (vendored), framer-motion, lucide-react.
  Analysis: Gemma 4 via OpenRouter, OpenAI-compatible; provider swap via
  `ANALYSIS_BASE_URL`/`ANALYSIS_API_KEY`/`ANALYSIS_MODEL` only. The
  hackathon's AMD-compute requirement is demonstrated separately (the real
  analysis prompt executed on an AMD Radeon gfx1100 GPU via ROCm/PyTorch —
  artifacts in `amd/`).
- **Rationale**: Pinned in CLAUDE.md ("Stack (do not substitute)");
  OpenAI-compatible endpoint makes any provider swap a config change, not a
  code change.
- **Alternatives considered**: Closed upstream — LangChain/LangGraph, other
  ORMs, and message queues are explicitly forbidden.

### S2. Fork/replay semantics

- **Decision**: Fork = new `runs` row (parent immutable); conversation-level
  replay from reconstructed `llm_call.input`; interception order positional →
  sha256 fallback → typed mock; temperature 0 default; verdicts on
  `run_metadata.detection`/`.analysis`.
- **Rationale**: Pinned decisions 1–4, 6; replay tests fidelity of context,
  not model chance; parent immutability makes forks safe and auditable.
- **Alternatives considered**: Closed upstream (program-level re-execution
  explicitly rejected in pinned decision 2).

### S3. Containerization

- **Decision**: Three compose services — backend, frontend, db — one image
  per service, wired by `docker compose up`; backend image doubles as the
  Railway deploy artifact; never a single combined image; SDK not
  containerized.
- **Rationale**: Pinned decision 7 (2026-07-06, maintainer decree).
- **Alternatives considered**: Backend-only image and monolithic image —
  both rejected by the maintainer when the decision was pinned.

## Resolved in this plan

### R1. API surface

- **Decision**: Five domains, six routes, all JSON, all behind
  `Authorization: Bearer $AGENTREPLAY_API_KEY`:
  - `POST /ingest` — batch of events (run upsert + step inserts)
  - `GET /runs` — list runs (filter: `agent_id`, `session_id`, `status`)
  - `GET /runs/{run_id}` — run + ordered steps (+ parent linkage for forks)
  - `POST /runs/{run_id}/fork` — body: `fork_step`, `modification`
    (e.g. edited system prompt), optional `temperature`; returns the new run
  - `POST /runs/{run_id}/analyze` — run root-cause analysis; store verdict
  - `POST /detect/sweep` — evaluate candidate runs (default candidates
    exclude `status=running` runs and forked runs, i.e. `parent_run_id`
    set); store verdicts + flag
- **Rationale**: One route per spec feature (FR-007/8, FR-010–13, FR-014–18,
  FR-019–20, FR-021–22); `POST /ingest` name is pinned in CLAUDE.md's
  architecture paragraph; routers per domain matches conventions.
- **Alternatives considered**: GraphQL (overkill, violates smallest-viable);
  per-step ingest route (chattier, contradicts batched fire-and-forget SDK);
  detection per-run only (sweep endpoint covers both: optional `run_ids`
  filter).

### R2. Ingest batching & idempotency

- **Decision**: The batch carries `run` header fields (id, agent_id,
  session_id, status, run_metadata, started_at/ended_at as known) plus a list
  of steps. Run row is upserted (insert-or-update of mutable fields: status,
  ended_at, run_metadata); steps are insert-only, protected by UNIQUE
  (run_id, seq); a duplicate/invalid step is rejected per-item with a
  per-item error in the response while valid items persist. HTTP 207-style
  body (200 with per-item results) rather than all-or-nothing. Upsert
  protections: ingest NEVER downgrades a `flagged` status (a late SDK batch
  reporting `completed` must not clear a detection flag), and the
  `run_metadata` merge NEVER removes or overwrites the `detection`/`analysis`
  keys (constitution VI) — merge, not replace.
- **Rationale**: SDK is fire-and-forget and may retry a batch after a
  timeout; idempotent upsert + per-item rejection means retries can never
  corrupt or duplicate (FR-008), and one bad event can't drop a whole
  conversation.
- **Alternatives considered**: All-or-nothing transaction per batch (a single
  duplicate from a retry would discard fresh steps); server-assigned seq
  (breaks verbatim positional replay matching — seq must be the recorder's
  truth).

### R3. canonical_json definition

- **Decision**: `canonical_json(args)` = `json.dumps(args, sort_keys=True,
  separators=(",", ":"), ensure_ascii=False)` encoded UTF-8. Fallback hash =
  `sha256((name + canonical_json(args)).encode("utf-8")).hexdigest()`.
  Implemented once in the backend (`app/replay/interceptor.py`) and covered
  by unit tests with fixed vectors.
- **Rationale**: Pinned decision 3 names `sha256(name + canonical_json(args))`
  but not the canonical form; sorted-keys/compact-separators is the standard
  deterministic serialization for Python dicts and is stable across processes.
- **Alternatives considered**: RFC 8785 JCS (full spec adds float
  canonicalization complexity V1 doesn't need — tool args here are
  strings/ints); pickle/repr hashing (not language-stable, not debuggable).

### R4. Single-shot fork execution (settled by maintainer 2026-07-06)

- **Decision**: A fork executes exactly ONE live llm_call at the fork step.
  The engine (a) loads parent steps 1..fork_step, (b) takes the recorded
  `llm_call.input` at (or nearest at-or-before) the fork step, (c) applies
  the modification (e.g. replace system message content), (d) calls the model
  live once (temperature 0 unless overridden) and records that single new
  llm_call step (`seq` 1 — the fork stores only this step; identity copied
  from parent: `agent_id`, `session_id`); the fork run is then marked
  `completed` (or `failed` on error). The engine does NOT walk subsequent
  parent steps, does NOT re-issue later llm_calls, does NOT reconstruct
  Nestaro's "Previous conversation" history format, and does NOT re-execute
  agent application code (pinned decision 2). The dashboard CompareView
  renders the fork's assistant text against the parent's step-K text AND the
  parent's subsequent tool_call step(s), with parent steps clearly labeled as
  parent-origin. The proof is that the model's decision flipped
  (Saturday → Friday); the fork never re-books anything.
  NOTE: the interceptor/tool-mock machinery (pinned decision 3, R3) is
  retained in the contract and its isolated tests as the generality guarantee
  for agents that DO emit LLM-native tool calls (V2/roadmap); it is simply
  not exercised by the Nestaro single-shot fork path — do not delete it as
  unused.
- **Rationale**: Nestaro's tools are NOT LLM-native (the request sends no
  tools array; tools are Python functions invoked after text parsing —
  docs/DATA_CONTRACT.md). A multi-step loop would therefore require either
  re-executing agent code (forbidden) or coupling the engine to Nestaro's
  history-formatting convention (fragile, agent-specific). Single-shot keeps
  replay purely conversation-level and still proves the fix: the flipped
  decision at the failing step.
- **Alternatives considered**: Walking the parent's remaining steps with
  positional interception and history re-assembly (rejected by maintainer —
  couples the engine to Nestaro's "Previous conversation" prompt format);
  agentic loop driven by model-emitted tool calls (inapplicable — Nestaro's
  requests carry no tools array, so the model cannot emit structured tool
  calls); re-executing agent FSM code (forbidden, pinned decision 2).

### R5. Detection & analysis via LLM-judge

- **Decision**: Both use the same OpenAI-compatible client on
  `ANALYSIS_BASE_URL` with Gemma 4. A run serializer renders steps into a
  compact transcript (system prompt, messages, tool calls + args + results,
  state changes). Detection prompt asks for strict JSON:
  `{"verdict": "pass|fail", "reason": str, "contradiction": {"user_intent":
  str, "agent_action": str} | null}` → stored at `run_metadata.detection`;
  on fail, run status → `flagged`. Analysis prompt asks for strict JSON:
  `{"failing_step": int, "root_cause": str, "suggested_fix": str}` → stored
  at `run_metadata.analysis`. JSON parsed defensively (extract first JSON
  object; on parse failure store nothing and return an error — FR edge case:
  "no verdict keys written with garbage").
- **Rationale**: Semantic contradiction (Friday vs Saturday) is inherently a
  language judgment — an LLM-judge is the settled analysis layer's purpose;
  strict-JSON prompts keep verdicts machine-renderable in the dashboard
  (FR-013, SC-006/7).
- **Alternatives considered**: Rule/regex detection (cannot generalize past
  the demo case; brittle even for it); embedding similarity (adds a model +
  threshold tuning for weaker explanations); vLLM guided/structured decoding
  (nice-to-have; prompt-level JSON + defensive parse is portable across
  OpenAI-compatible providers).

### R6. Fork live-inference endpoint

- **Decision**: Forked LLM calls go to an OpenAI-compatible endpoint
  configured by `REPLAY_BASE_URL` + `REPLAY_API_KEY`, defaulting to
  OpenRouter (`https://openrouter.ai/api/v1`), reusing the recorded
  `model` id from the parent `llm_call.input`.
- **Rationale**: Recorded runs carry OpenRouter-style ids
  (`deepseek/deepseek-chat`); replay fidelity means calling the same model
  the parent used, and pinning the switch to env vars mirrors the
  `ANALYSIS_BASE_URL` pattern already settled for analysis.
- **Alternatives considered**: Routing forks to the Gemma 4 analysis endpoint
  (different model family — would invalidate "verify the fix against the
  conversation that failed"); hardcoding OpenRouter (violates env-only
  config).

### R7. Local db service & schema creation

- **Decision**: Compose `db` service = official `postgres:16` image with a
  named volume; backend runs `SQLModel.metadata.create_all` on startup
  (idempotent) — no migration tool in V1. NeonDB is used by the hosted
  deploy via the same `DATABASE_URL` env var.
- **Rationale**: Two tables, hackathon timeline; create_all is the smallest
  viable schema bootstrap and identical in and out of containers
  (constitution VII: no container-specific code paths).
- **Alternatives considered**: Alembic migrations (right for post-V1, more
  moving parts than a 2-table demo warrants; nothing in the scope guard or
  contract requires versioned migrations yet).

**All unknowns resolved — no NEEDS CLARIFICATION remain. Phase 1 may proceed.**
