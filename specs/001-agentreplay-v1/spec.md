# Feature Specification: AgentReplay V1

**Feature Branch**: `001-agentreplay-v1`
**Created**: 2026-07-04
**Status**: Draft
**Input**: User description: "AgentReplay V1: flight recorder and time-travel debugger for AI agents. Frozen feature set: Python SDK (record llm_call/tool_call/state_change steps), ingest API, timeline dashboard, replay/fork engine, analysis layer, detection sweep. Transcribe the data contract from docs/DATA_CONTRACT.md byte-identical (field names, enums, payload shapes). Primary acceptance scenario: recorded Nestaro run where customer asks for Friday but agent books Saturday — detect via semantic contradiction, root-cause analysis with suggested prompt fix, fork from failing step with fix applied (live inference, intercepted tool calls, no real booking), show forked run booking Friday alongside original booking Saturday. Transcribe and formalize only — do not redesign."

> This spec TRANSCRIBES settled design documents. `docs/DATA_CONTRACT.md` is the
> law for all data shapes; `docs/DECISIONS.md` (mirrored in the project
> constitution) is the law for architectural behavior. Nothing here redesigns,
> renames, or restructures those sources. If this spec and those documents ever
> disagree, STOP and reconcile with the maintainer.

## Frozen Feature Set *(V1 — exactly these six, no more)*

1. **SDK** — a Python library the host agent embeds to record every step of
   its execution (llm_call, tool_call, state_change) invisibly.
2. **Ingest API** — the backend surface that receives recorded events in
   batches and persists them according to the data contract.
3. **Timeline dashboard** — a web UI listing runs and rendering each run's
   step-by-step timeline, including side-by-side parent/fork comparison.
4. **Replay/fork engine** — forks a recorded run from any step with a user
   modification, using live inference and intercepted (never real) tool calls.
5. **Analysis layer** — sends a serialized run to an analysis model and stores
   a structured root-cause verdict on the run's metadata.
6. **Detection sweep** — evaluates recorded runs for failures (e.g. semantic
   contradiction between user intent and agent action) and flags them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Debug the Friday/Saturday booking failure end-to-end (Priority: P1)

**This scenario is the product; the spec exists to make it real.** A developer
operating Nestaro (a lead-qualification agent for home service businesses) has
a recorded run in which the customer asked for a Friday appointment but the
agent booked Saturday. Using AgentReplay, the developer discovers the failure,
understands its root cause, verifies a fix against the exact conversation that
failed — without any real-world side effect — and sees the corrected outcome
next to the original.

**Why this priority**: This is the north-star acceptance scenario. Every other
capability exists to make this journey possible. If only this story ships, the
product's core value — time-travel debugging of a real agent failure — is
demonstrated.

**Independent Test**: Seed the system with the recorded Nestaro
Friday/Saturday run, then walk steps (a)–(d) below in order against a live
system. The story passes only if all four steps pass.

**Acceptance Scenarios**:

1. **Given** a recorded Nestaro run where the customer asks for Friday and the
   agent books Saturday, **When** the detection sweep evaluates the run,
   **Then** the run is detected as failed/flagged via semantic contradiction
   (the run's `status` becomes `flagged` and a detection verdict is
   stored under `run_metadata.detection`).
2. **Given** the flagged run, **When** the developer requests analysis,
   **Then** the system produces a root-cause analysis identifying the failing
   step and a suggested prompt fix, stored under `run_metadata.analysis`.
3. **Given** the analysis identifying the failing step and suggested fix,
   **When** the developer forks the run from the failing step with the fix
   applied, **Then** the fork executes exactly ONE live LLM call from the
   reconstructed, modified context at that step (temperature 0 unless
   overridden) — no tool is invoked and no real booking occurs (Nestaro's
   tools are not LLM-native; the fork never re-books anything).
4. **Given** the completed fork, **When** the developer views the comparison,
   **Then** the dashboard shows the fork's assistant reply choosing Friday
   alongside the original run's step-K assistant text and its subsequent
   `book_appointment` tool_call (saturday), parent steps clearly labeled as
   parent-origin — the proof is that the model's decision flipped
   (Saturday → Friday).

---

### User Story 2 - Record an agent run invisibly and inspect its timeline (Priority: P2)

A developer instruments their agent with the SDK. The agent runs normally —
its users notice nothing, and the agent's behavior is unchanged even if the
recording backend is down. Afterwards, the developer opens the dashboard,
finds the run, and inspects every step in order: each LLM call with its exact
request and response, each tool call with its exact args and result, each
state change with its trigger.

**Why this priority**: Recording is the substrate for everything else — no
recorded run, nothing to detect, analyze, or fork. It is P2 only because on
its own it demonstrates observability, not the differentiating fork
capability.

**Independent Test**: Run an instrumented agent conversation end-to-end,
then verify via the dashboard (and directly against the ingest API) that every
step appears, in sequence, with verbatim payloads matching what the agent
actually sent and received.

**Acceptance Scenarios**:

1. **Given** an agent instrumented with the SDK, **When** the agent executes a
   conversation involving LLM calls, tool calls, and state changes, **Then**
   every step is persisted with correct `type`, 1-based contiguous `seq`, and
   verbatim `input`/`output` payloads per the data contract.
2. **Given** the recording backend is unreachable, **When** the instrumented
   agent runs, **Then** the agent completes its work with no error raised into
   host agent code and no visible change in behavior; transport errors are
   swallowed and logged locally.
3. **Given** a persisted run, **When** the developer opens it in the
   dashboard, **Then** the timeline renders all steps in `seq` order showing
   the recorded payloads without summarizing or trimming.

---

### User Story 3 - Sweep recorded runs for failures (Priority: P3)

A developer has many recorded runs and cannot read them all. They trigger the
detection sweep, which evaluates completed runs and flags those where the
agent's actions contradict the user's expressed intent, so the developer's
attention goes straight to the broken conversations.

**Why this priority**: Detection turns a pile of recordings into a short list
of problems. It depends on recording (US2) and feeds analysis/forking (US1).

**Independent Test**: Seed at least one contradictory run (Friday asked,
Saturday booked) and at least one correct run; trigger the sweep; verify only
the contradictory run is flagged and carries a detection verdict.

**Acceptance Scenarios**:

1. **Given** a set of recorded runs including at least one with a semantic
   contradiction between user request and agent action, **When** the detection
   sweep executes, **Then** the contradictory run's `status` is set to
   `flagged` and a detection verdict is stored under
   `run_metadata.detection`.
2. **Given** a recorded run with no contradiction, **When** the detection
   sweep executes, **Then** that run is not flagged.

---

### User Story 4 - Fork safely: sandboxed tools, deterministic inference (Priority: P3)

A developer forks a run whose recorded steps include real-world tool calls
(e.g. booking an appointment). Fork inference is deterministic unless the
developer explicitly overrides, the parent is never touched, and the tool
interception contract holds: any tool call a replayed model ever emits is
answered from the recording or a typed mock — never executed for real.

NOTE: Nestaro's tools are NOT LLM-native (no tools array is sent), so the V1
single-shot fork path never emits tool calls. The interceptor and its tests
are retained deliberately as the generality guarantee for agents that DO
emit tool calls (V2/roadmap) — do not delete them as unused.

**Why this priority**: This is the safety and trust contract of the fork
engine. It is exercised inside US1 but must also hold for arbitrary forks.

**Independent Test**: Exercise the interceptor directly against a recorded
run's tool_call steps to verify the pinned matching order and the typed
mock, with a sentinel proving zero real tool executions; fork a run to
verify temperature policy and parent immutability.

**Acceptance Scenarios**:

1. **Given** a replayed model that requests a tool call (a tool-emitting
   agent — not Nestaro's single-shot path), **When** the interceptor resolves
   it, **Then** the system matches a cached result by (run_id, seq)
   positionally; if that fails, by sha256(name + canonical_json(args)); and if
   no match exists, returns the typed mock `{"result": {"mocked": true},
   "error": null}` — and in no case executes a real tool.
2. **Given** a fork request with no temperature override, **When** forked LLM
   calls execute, **Then** they run at temperature 0.
3. **Given** a fork request with an explicit temperature override, **When**
   forked LLM calls execute, **Then** they use the overridden temperature.
4. **Given** a completed fork, **When** the parent run and its steps are
   inspected, **Then** they are byte-for-byte unchanged: the fork exists only
   as a new run row with `parent_run_id` and `fork_step` set.

---

### Edge Cases

- **Backend down mid-run**: SDK buffers/flushes fire-and-forget; all transport
  errors are swallowed and logged locally; the host agent never sees an
  exception (pinned decision 5).
- **Fork tool call with no cached match** (a tool-emitting replayed model
  calls a tool that was never recorded): return the typed mock
  `{"result": {"mocked": true}, "error": null}` (pinned decision 3;
  interceptor-level guarantee — not exercised by Nestaro's single-shot path).
- **Duplicate (run_id, seq)** submitted to ingest: rejected by the UNIQUE
  constraint on (run_id, seq); ingest must surface a validation error for the
  offending event without corrupting stored steps.
- **Fork requested at a `seq` that is not an `llm_call` step**: replay is
  conversation-level; the engine must reconstruct from the recorded
  `llm_call.input` context at the fork point. If the request is invalid (no
  reconstructable LLM context), the fork request fails with a clear error and
  no fork run is created.
- **Run never ended** (agent crashed before completion): run remains in
  `status = running` with `ended_at` null; dashboard renders it; detection
  sweep handles/skips it without error.
- **Detection or analysis model unavailable**: sweep/analysis fails gracefully
  with an error result; recorded runs are never modified or lost; no verdict
  keys are written with garbage.
- **Non-JSON-serializable or oversized payloads**: payloads are recorded
  verbatim as sent/received; the system must not summarize or trim them
  (data contract). If a payload cannot be recorded, that is a recording error
  handled per pinned decision 5 (swallowed, logged, invisible to host).

## Requirements *(mandatory)*

### Functional Requirements

**Recording (SDK)**

- **FR-001**: The SDK MUST record every step of an instrumented agent's
  execution as one of exactly three types: `llm_call`, `tool_call`,
  `state_change`.
- **FR-002**: The SDK MUST record payloads verbatim — the EXACT request sent
  to the model (the messages array in order, including the optional
  "Previous conversation" history message, plus params and the HTTP-Referer/
  X-Title headers, per the Data Contract) and the EXACT response received —
  never summarized, never trimmed. (Nestaro sends a bare single-shot text
  completion: no tools array, no tool_choice, no response_format, no
  streaming.)
- **FR-003**: The SDK MUST assign each step a 1-based, per-run sequence number
  `seq`.
- **FR-004**: The SDK MUST buffer events in memory and deliver them to the
  ingest API in batches, fire-and-forget.
- **FR-005**: The SDK MUST never raise into host agent code. All
  transport/recording errors are swallowed and logged locally; a recording
  failure MUST be invisible to the agent it records.
- **FR-006**: The SDK MUST record, where applicable, `latency_ms` per step and
  `tokens_in`/`tokens_out` for `llm_call` steps.
- **FR-027**: The SDK MUST NEVER record the Authorization header or any
  bearer token — redaction happens at the SDK boundary before buffering. A
  recorded `llm_call.input` MUST NOT contain an Authorization key at any
  level. (The fork engine supplies its own credentials; it needs the messages
  and params to replay, not the original auth.)

**Ingest API**

- **FR-007**: The ingest API MUST accept batched recorded events and persist
  runs and steps exactly per the Data Contract below.
- **FR-008**: The ingest API MUST validate incoming events against the Data
  Contract and reject events that violate it (including duplicate
  (run_id, seq)) without corrupting previously stored data.
- **FR-009**: Access to the API MUST be protected by a single static API key
  and nothing more (scope guard: no additional auth in V1).

**Timeline dashboard**

- **FR-010**: The dashboard MUST list recorded runs with their `agent_id`,
  `session_id`, `status`, and timing, and indicate flagged/failed runs.
- **FR-011**: The dashboard MUST render a run's timeline: all steps in `seq`
  order with type-appropriate display of the recorded `input`/`output`
  payloads, unsummarized.
- **FR-012**: The dashboard MUST display fork lineage (`parent_run_id`,
  `fork_step`) and show a forked run alongside its parent for comparison:
  the fork's assistant text rendered against the parent's step-K text AND
  the parent's subsequent tool_call step(s), with parent steps clearly
  labeled as parent-origin — for the primary scenario, the fork's reply
  choosing Friday next to the original's Saturday decision and its
  `book_appointment` (saturday) tool_call. The proof is the flipped decision;
  the fork never re-books anything.
- **FR-013**: The dashboard MUST display detection and analysis verdicts read
  from `run_metadata.detection` and `run_metadata.analysis`.

**Replay/fork engine**

- **FR-014**: A fork MUST be created as a new row in `runs` with
  `parent_run_id` and `fork_step` set. The parent run and its steps MUST NEVER
  be modified.
- **FR-015**: Replay MUST be conversation-level, not program-level: the engine
  reconstructs the recorded `llm_call.input` at the fork step, applies the
  user's modification (e.g. an edited system prompt), and calls the model live
  from there. The engine MUST NOT re-execute the agent's application code. In
  V1 a fork executes exactly ONE live LLM call at the fork step and stores
  that single new step; it does NOT walk subsequent parent steps, re-issue
  later llm_calls, or reconstruct Nestaro's "Previous conversation" history
  format.
- **FR-016**: If a replayed model emits a tool call, it MUST be intercepted
  and resolved in this exact order: (1) match cached result by (run_id, seq)
  positionally; (2) fallback match by sha256(name + canonical_json(args));
  (3) no match → return typed mock `{"result": {"mocked": true}, "error":
  null}`. A forked run MUST NEVER execute a real tool. No exceptions, no side
  effects. NOTE: Nestaro's single-shot fork path emits no tool calls; this
  machinery is the generality guarantee for tool-emitting agents
  (V2/roadmap) — keep it and its tests even though the demo path does not
  exercise it.
- **FR-017**: Forked LLM calls MUST run at temperature 0 unless the fork
  request explicitly overrides.
- **FR-018**: Forked runs and their steps MUST be recorded under the same Data
  Contract as original runs, so forks are themselves inspectable and
  comparable.

**Analysis layer**

- **FR-019**: The analysis layer MUST send a serialized recorded run to the
  analysis model and produce a structured root-cause verdict that identifies
  the failing step and a suggested prompt fix.
- **FR-020**: Analysis verdicts MUST be stored as JSONB on the run's metadata
  under `run_metadata.analysis`.

**Detection sweep**

- **FR-021**: The detection sweep MUST evaluate recorded runs and detect
  failures including semantic contradiction between the user's expressed
  intent and the agent's action (e.g. customer asks for Friday, agent books
  Saturday).
- **FR-022**: Detection verdicts MUST be stored as JSONB on the run's metadata
  under `run_metadata.detection`, and detected runs MUST be marked by setting
  the run `status` to `flagged`.

**Docker containerization (mandatory delivery step — constitution Principle VII)**

- **FR-023**: The backend (ingest API + replay/fork engine + analysis/
  detection) MUST ship as a Docker image built from a Dockerfile in the repo,
  and the deployed backend MUST run as that container.
- **FR-024**: The dashboard MUST have its own Dockerfile so it can run as a
  container for local/demo use.
- **FR-025**: The repo MUST provide a compose file such that `docker compose
  up` wires up the full local stack as three separate services — backend,
  frontend (dashboard), and db (Postgres) — one image/container per service,
  never a single combined image.
- **FR-026**: Containerized components MUST be configured via environment
  variables only, with no secrets baked into images and no
  container-specific code paths: behavior inside a container is identical to
  behavior outside it, including every guarantee of the Data Contract.
  (The SDK is a Python library embedded in host agents; it is not
  containerized.)

### Data Contract *(transcribed byte-identical from docs/DATA_CONTRACT.md — the law)*

Every component obeys this: the SDK writes it, ingest validates it, the
timeline renders it, the fork engine reads it, the tests assert it. Do not
add, rename, or drop fields without updating `docs/DATA_CONTRACT.md` first.

#### Table: runs

- id: UUID pk
- agent_id: str, indexed
- session_id: str, indexed (e.g. FB Messenger sender id)
- status: enum(running, completed, failed, flagged)
- parent_run_id: UUID fk -> runs.id, nullable (set only on forks)
- fork_step: int, nullable (seq in parent where this fork diverged)
- run_metadata: JSONB (channel, business_id, detection verdict, analysis
  verdict, freeform)
- started_at, ended_at: timestamptz

#### Table: steps

- id: UUID pk
- run_id: UUID fk -> runs.id, indexed
- seq: int (1-based per run; UNIQUE constraint on (run_id, seq))
- type: enum(llm_call, tool_call, state_change)
- input: JSONB   (shape depends on type — see below)
- output: JSONB  (shape depends on type — see below)
- latency_ms: int, nullable
- tokens_in, tokens_out: int, nullable (llm_call only)
- created_at: timestamptz

#### Payload shapes — VERBATIM recording, never summarize or trim

llm_call.input — the EXACT request sent to the model

Nestaro sends a bare single-shot text completion: no tools, no tool_choice,
no response_format, no streaming. Record exactly these fields:

```json
{
  "model": "deepseek/deepseek-chat",
  "messages": [
    {"role": "system", "content": "<full system prompt as sent>"},
    {"role": "user", "content": "Previous conversation:\n<history>"},
    {"role": "user", "content": "I need duct cleaning Friday"}
  ],
  "max_tokens": 1024,
  "temperature": 0.7,
  "headers": {"HTTP-Referer": "https://nestaro.com",
              "X-Title": "Nestaro Lead Qualifier"}
}
```

RULES:
- The messages array is recorded EXACTLY as sent, in order. The optional
  second `user` message ("Previous conversation:\n...") is part of the
  context the model saw and MUST be captured verbatim in position — the fork
  engine reconstructs from this, so any drift here corrupts replay.
- Record HTTP-Referer and X-Title for fidelity. NEVER record the
  Authorization header or any bearer token — redact at the SDK boundary.
- The fork engine supplies its own credentials; it needs the messages and
  params to replay, not the original auth.

llm_call.output — the EXACT response received:

```json
{
  "id": "gen-abc123",
  "choices": [{"message": {"role": "assistant",
    "content": "<full assistant reply>"}, "finish_reason": "stop"}],
  "usage": {"prompt_tokens": 512, "completion_tokens": 87}
}
```

tool_call.input:

NOTE: In Nestaro, tools are NOT LLM-native function calls (the request sends
no tools array). A tool_call is a real Python function with side effects
(e.g. book_appointment) invoked after the text response is parsed, captured
via the `@replay.tool` decorator. These are what the fork engine intercepts.

```json
{"name": "book_appointment",
 "args": {"day": "saturday", "time": "14:00", "customer_id": "cust_991"}}
```

tool_call.output:

```json
{"result": {"booking_id": "bk_204", "confirmed": true}, "error": null}
```

state_change.input / .output:

```json
{"from_state": "QUOTING", "to_state": "BOOKING", "trigger": "user_confirmed"}
```

### Key Entities

- **Run**: One recorded agent execution (or one fork of one). Identified by
  `id`; owned by an `agent_id` and a `session_id`; carries lifecycle `status`
  (running, completed, failed, flagged), timing (`started_at`, `ended_at`),
  freeform `run_metadata` (including `detection` and `analysis` verdicts), and
  — when it is a fork — lineage via `parent_run_id` and `fork_step`.
- **Step**: One recorded event inside a run, ordered by 1-based `seq` (unique
  per run). Exactly one of three types — `llm_call`, `tool_call`,
  `state_change` — each with type-specific verbatim `input`/`output` payloads,
  plus optional `latency_ms` and (for `llm_call`) `tokens_in`/`tokens_out`.
- **Detection verdict**: Structured result of the detection sweep for a run,
  stored under `run_metadata.detection`.
- **Analysis verdict**: Structured root-cause result for a run — identifying
  the failing step and a suggested prompt fix — stored under
  `run_metadata.analysis`.

## Out of Scope — NOT in V1 *(scope guard, from docs/DECISIONS.md)*

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

## Assumptions

- The primary acceptance scenario's Nestaro run is available as a recorded run
  (recorded live via the SDK or seeded as a fixture that conforms to the Data
  Contract); the spec does not require Nestaro's own codebase to be part of
  this system.
- "Detected as failed/flagged" means the detection sweep sets the run's
  `status` to `flagged` (settled in planning; `failed` remains in the enum
  for runs that error during execution). Both statuses mark the run for the
  developer's attention in the dashboard.
- The detection sweep is triggered on demand (e.g. by the developer or the
  demo flow); no scheduling/streaming machinery is implied (scope guard:
  no streaming ingestion).
- Fork comparison in the dashboard is a side-by-side view of the parent and
  fork timelines; exact visual layout is a planning/design concern.
- Fork execution model (settled by maintainer 2026-07-06): a fork executes
  exactly ONE live LLM call at the fork step (single-shot) and stores that
  single new step. The comparison proof is the flipped model decision
  (Saturday → Friday); the fork never re-books. The tool interceptor remains
  in the contract as the generality guarantee for tool-emitting agents.
- Docker containerization scope (added 2026-07-06, confirmed by maintainer):
  full-stack containerization via compose — one image/container per service
  (backend, frontend, db), never a single combined image; `docker compose up`
  wires up all three. The backend image is also the deploy artifact; the
  frontend Dockerfile serves local/demo use (hosted dashboard remains on its
  existing platform). The SDK, as an embedded library, is not containerized.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The primary acceptance scenario passes end-to-end: from a
  recorded Friday/Saturday Nestaro run, the developer reaches a side-by-side
  view of the fork booking Friday and the original booking Saturday, with
  zero real bookings (or any other real tool effect) triggered by the fork.
- **SC-002**: 100% of steps of an instrumented agent conversation appear in
  the stored run with correct type, contiguous 1-based sequence, and payloads
  byte-identical to what the agent sent and received (with the Authorization
  header redacted per FR-027 — it never appears in any recorded payload).
- **SC-003**: An instrumented agent completes its conversation successfully
  with the recording backend fully unreachable, with zero errors surfaced to
  the agent or its end user.
- **SC-004**: Across any forked run, the number of real tool executions is
  exactly zero, and every intercepted tool call resolves per the pinned
  matching order (positional → hash → typed mock) — tier order verified at
  interceptor level, since Nestaro's single-shot forks issue no tool calls.
- **SC-005**: After a fork completes, the parent run and its steps are
  unchanged (verifiable by comparing before/after snapshots).
- **SC-006**: The detection sweep flags the seeded contradictory run and does
  not flag the seeded correct run.
- **SC-007**: For a flagged run, the analysis verdict names a failing step
  that exists in the run and includes a non-empty suggested prompt fix, and
  both verdicts are readable from the dashboard.
- **SC-008**: From a clean checkout, `docker compose up` brings up the full
  local stack as three separate containers (backend, frontend, db), and the
  primary acceptance scenario (SC-001) passes end-to-end against that
  containerized stack.
