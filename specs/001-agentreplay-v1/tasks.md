# Tasks: AgentReplay V1

**Input**: Design documents from `/specs/001-agentreplay-v1/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.openapi.yaml, quickstart.md

**Tests**: INCLUDED — the constitution makes tests the enforcement mechanism of
the data contract ("the tests assert it") and session rules define done as
acceptance criteria passing under pytest. Test tasks are written BEFORE the
implementation they verify and MUST fail first. Reminder: implementation
sessions NEVER modify files under `tests/` — test files are created only by
their own dedicated test tasks below.

**Organization**: Tasks are grouped by user story (spec.md US1–US4) so each
story is an independently testable increment. Session rule: execute exactly
ONE task per session; commit as `T-NN: <what>`; append to PROGRESS.md.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Include exact file paths in descriptions

## Path Conventions

Per plan.md structure: backend in `app/`, SDK in `sdk/agentreplay/`,
dashboard in `dashboard/`, tests in `tests/{contract,integration,unit}/`,
scripts in `scripts/`, containers via root `Dockerfile`, `dashboard/Dockerfile`,
root `compose.yml`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project skeleton + the three-container stack (constitution VII)

- [X] T001 Create project structure per plan.md: `app/` (with `routers/`, `replay/`, `analysis/` subdirs + `__init__.py` files), `sdk/agentreplay/`, `dashboard/`, `tests/contract/`, `tests/integration/`, `tests/unit/`, `scripts/`
- [X] T002 Initialize backend Python project: `pyproject.toml` (python 3.11+, fastapi, sqlmodel, httpx, psycopg[binary], uvicorn, pytest, respx) and minimal `app/main.py` FastAPI app with `GET /health` returning `{"ok": true}`; acceptance: `uvicorn app.main:app` serves /health
- [X] T003 [P] Initialize Next.js + TypeScript + Tailwind app in `dashboard/` (no UI library beyond Tailwind); acceptance: `npm run dev` renders a placeholder page
- [X] T004 [P] Create `.env.example` with DATABASE_URL, AGENTREPLAY_API_KEY, ANALYSIS_BASE_URL, ANALYSIS_API_KEY, REPLAY_BASE_URL, REPLAY_API_KEY (no real values — constitution: no hardcoded secrets)
- [X] T005 Write backend image `Dockerfile` at repo root (python 3.11 slim, installs backend including dev deps pytest/respx and the `tests/` directory so `docker compose exec backend pytest` works per quickstart.md, runs uvicorn on :8000, config via env only)
- [X] T006 [P] Write frontend image `dashboard/Dockerfile` (node build → next start on :3000, config via env only)
- [X] T007 Write root `compose.yml` wiring exactly three services — backend (root Dockerfile), frontend (dashboard/Dockerfile), db (postgres:16 + named volume) — one container per service, never a combined image; acceptance: `docker compose up` starts all three and `curl localhost:8000/health` succeeds (constitution VII / SC-008 substrate)

**Checkpoint**: `docker compose up` brings up backend + frontend + db

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data contract in code + ingest/read API + demo fixture — every
user story's independent test needs these to get a run in and read it back

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Create SQLModel entities `Run` and `Step` in `app/models.py` mirroring data-model.md field-for-field: enums (running/completed/failed/flagged; llm_call/tool_call/state_change) byte-identical, JSONB columns, UNIQUE (run_id, seq), indexes on agent_id/session_id/run_id (constitution: Data Contract Supremacy)
- [X] T009 Create `app/db.py` (engine/session from DATABASE_URL, `SQLModel.metadata.create_all` on startup per research R7) and wire into `app/main.py` lifespan
- [X] T010 Implement static API key auth dependency (Authorization: Bearer $AGENTREPLAY_API_KEY) in `app/main.py` and apply to all routers; nothing beyond one static key (scope guard, FR-009)
- [X] T011 [P] Create pydantic schemas in `app/schemas.py` per contracts/api.openapi.yaml: IngestBatch, IngestResult, RunOut, StepOut, RunDetail, ForkRequest, AnalysisVerdict, DetectionVerdict, SweepResult, Error
- [X] T012 Write contract tests (must fail now): `tests/contract/test_ingest.py` (valid batch persists verbatim payloads; duplicate (run_id, seq) rejected per-item while valid items persist; bad enum rejected; missing key → 401) and `tests/contract/test_runs.py` (list + detail with steps ordered by seq, fork lineage fields present)
- [X] T013 Implement `POST /ingest` in `app/routers/ingest.py` per research R2: upsert run header (status, ended_at, run_metadata merge), insert-only steps under UNIQUE (run_id, seq), per-item rejection response; upsert protections — never downgrade a `flagged` status and never remove/overwrite `run_metadata.detection`/`.analysis` keys (FR-007, FR-008, constitution VI); acceptance: T012 ingest tests pass
- [X] T014 Implement `GET /runs` (filters: agent_id, session_id, status, limit/offset) and `GET /runs/{run_id}` (run + steps ordered by seq) in `app/routers/runs.py`; acceptance: T012 runs tests pass
- [X] T015 [P] Write `scripts/seed_demo_run.py`: POSTs the Nestaro Friday/Saturday fixture to /ingest — a completed run whose steps include the recorded system prompt, the "Previous conversation:\n..." history user message in position, user "I need duct cleaning Friday", HTTP-Referer/X-Title headers (and NO Authorization key), llm_call outputs, `book_appointment` tool_call with args day="saturday", state_changes — payload shapes byte-identical to docs/DATA_CONTRACT.md; acceptance: run visible via GET /runs

**Checkpoint**: Foundation ready — a data-contract-conformant run can be ingested, stored, and read back

---

## Phase 3: User Story 1 - Debug the Friday/Saturday booking failure end-to-end (Priority: P1) 🎯 MVP

**Goal**: The product. From the seeded contradictory run: detect (flag +
verdict) → analyze (failing step + suggested fix) → single-shot fork at the
failing step with fix at temperature 0 (exactly one live llm_call; no tool
invoked, zero real bookings) → dashboard shows the fork's Friday decision
beside the original's Saturday decision and parent-labeled booking.

**Independent Test**: quickstart.md steps 2–6 against the compose stack using
the seeded fixture (no SDK needed — spec assumption allows seeded runs).

### Tests for User Story 1 (write first, must fail) ⚠️

- [ ] T016 [P] [US1] Integration test in `tests/integration/test_detection.py`: with a stubbed OpenAI-compatible analysis endpoint (respx), POST /detect/sweep flags the seeded run, writes DetectionVerdict JSON at run_metadata.detection, sets status=flagged; on unparseable model output writes nothing and returns error (FR-021/22, edge case)
- [ ] T017 [P] [US1] Integration test in `tests/integration/test_analysis.py`: POST /runs/{id}/analyze (stubbed endpoint) stores {failing_step, root_cause, suggested_fix} at run_metadata.analysis where failing_step exists in the run; 502 + run unchanged on model failure (FR-019/20, SC-007)
- [ ] T018 [P] [US1] Integration test in `tests/integration/test_fork.py`: POST /runs/{id}/fork with modification (stubbed replay endpoint returning an assistant reply that decides friday) creates a NEW run with parent_run_id + fork_step and agent_id/session_id copied from parent, containing exactly ONE llm_call step (seq 1, temperature 0 recorded in its input) under the data contract, executes zero real tools, and parent rows are byte-identical before/after (FR-014/15/17/18, SC-004/5, research R4 single-shot)

### Implementation for User Story 1

- [ ] T019 [P] [US1] Create OpenAI-compatible chat client in `app/analysis/client.py` reading ANALYSIS_BASE_URL/ANALYSIS_API_KEY (research R5; Fireworks fallback = env swap only)
- [ ] T020 [P] [US1] Create run serializer in `app/analysis/serializer.py`: steps → compact transcript (system prompt, messages, tool calls with args/results, state changes) for judge prompts
- [ ] T021 [P] [US1] Create strict-JSON prompt templates in `app/analysis/prompts.py`: detection verdict {verdict, reason, contradiction} and analysis verdict {failing_step, root_cause, suggested_fix} with defensive JSON extraction helper (research R5)
- [ ] T022 [US1] Implement `POST /detect/sweep` in `app/routers/detection.py`: evaluate candidate runs (skip status=running), merge verdict into run_metadata.detection, set status=flagged on fail; acceptance: T016 passes
- [ ] T023 [US1] Implement `POST /runs/{run_id}/analyze` in `app/routers/analysis.py`: serialize run → judge → merge verdict into run_metadata.analysis; acceptance: T017 passes
- [ ] T024 [US1] Implement tool interceptor in `app/replay/interceptor.py`: canonical_json (sort_keys, separators=(",", ":"), UTF-8) + sha256(name + canonical_json(args)); resolution order positional (run_id, seq) → hash → typed mock {"result": {"mocked": true}, "error": null}; module exposes NO code path to real tool execution (constitution III, research R3)
- [ ] T025 [US1] Implement replay engine in `app/replay/engine.py` (single-shot per research R4): load parent steps 1..fork_step, reconstruct recorded llm_call.input at-or-before fork step, apply modification (system_prompt replacement), execute exactly ONE live model call via REPLAY_BASE_URL at temperature 0 (unless override), record that single llm_call step (seq 1); do NOT walk subsequent parent steps, re-issue later llm_calls, reconstruct Nestaro's "Previous conversation" history format, or re-execute agent code; fork run created with parent_run_id + fork_step, agent_id/session_id copied from parent, marked completed/failed (constitution I/II/IV, research R4/R6)
- [ ] T026 [US1] Implement `POST /runs/{run_id}/fork` in `app/routers/fork.py`: validate fork_step (422 + no fork run when no reconstructable llm_call context), execute engine, return 201 RunDetail; acceptance: T018 passes
- [ ] T027 [P] [US1] Create typed API client in `dashboard/src/lib/api.ts` for /runs, /runs/{id}, /fork, /analyze, /detect/sweep with TS types mirroring contracts/api.openapi.yaml
- [ ] T028 [US1] Build runs list page `dashboard/src/app/page.tsx`: agent_id, session_id, status badges (flagged/failed highlighted), timing, fork lineage indicator (FR-010)
- [ ] T029 [US1] Build run detail page `dashboard/src/app/runs/[id]/page.tsx` + `dashboard/src/components/TimelineStep.tsx` + `dashboard/src/components/VerdictBadge.tsx`: timeline in seq order with type-appropriate verbatim payload rendering (expandable, unsummarized) and detection/analysis verdict display (FR-011, FR-013)
- [ ] T030 [US1] Build fork + compare UI: `dashboard/src/components/ForkPanel.tsx` (pick step, edit system prompt prefilled from recorded input + suggested_fix, optional temperature) and `dashboard/src/components/CompareView.tsx` (side-by-side per research R4 single-shot: the fork's assistant text rendered against the parent's step-K text AND the parent's subsequent tool_call step(s), parent steps clearly labeled as parent-origin — the proof is the flipped decision, saturday → friday) wired into run detail page (FR-012)
- [ ] T031 [US1] End-to-end acceptance against live compose stack: run quickstart.md steps 1–6 (up → seed → sweep → analyze → fork → compare) with real ANALYSIS_BASE_URL and REPLAY_BASE_URL; verify SC-001 and record evidence (run ids, screenshots) in PROGRESS.md

**Checkpoint**: The demo works — MVP complete (SC-001)

---

## Phase 4: User Story 2 - Record an agent run invisibly and inspect its timeline (Priority: P2)

**Goal**: Python SDK records llm_call/tool_call/state_change verbatim,
batched fire-and-forget, and can never raise into host code; a live-recorded
run renders on the (already built) timeline.

**Independent Test**: run `scripts/demo_agent.py` (instrumented sample agent)
against the local stack; every step appears in order with verbatim payloads
(verifiable via `GET /runs/{id}` directly if the US1 dashboard is not built
yet); repeat with backend stopped — agent completes with zero errors.

### Tests for User Story 2 (write first, must fail) ⚠️

- [ ] T032 [P] [US2] Unit tests in `tests/unit/test_sdk_buffer.py`: buffer accumulates events, assigns contiguous 1-based seq, flushes in batches shaped as IngestBatch (FR-003, FR-004)
- [ ] T033 [P] [US2] Unit tests in `tests/unit/test_sdk_wrapper.py`: wrapped client records llm_call input/output byte-identical to what was sent/received (messages array in order including the "Previous conversation" history message, params, HTTP-Referer/X-Title headers), latency_ms and tokens_in/out populated, AND a recorded llm_call.input never contains an Authorization key at any level (FR-002, FR-006, FR-027)
- [ ] T034 [P] [US2] Integration test in `tests/integration/test_sdk_never_raises.py`: with transport pointed at a dead port and at an erroring server, wrapped calls + tool calls + flush complete without raising; errors logged locally only (FR-005, SC-003, constitution V)

### Implementation for User Story 2

- [ ] T035 [US2] Create SDK package skeleton: `sdk/agentreplay/__init__.py` exposing `init(base_url, api_key, agent_id)`, `wrap`, `tool`, `record_state_change`, `end_run(status="completed")` (finalizes the run: sets status + ended_at and flushes — without it recorded runs stay `running` and the sweep skips them), `flush`; `sdk/pyproject.toml` (httpx only runtime dep)
- [ ] T036 [US2] Implement `sdk/agentreplay/buffer.py` (in-memory event buffer, seq assignment, batch assembly) and `sdk/agentreplay/transport.py` (httpx fire-and-forget POST /ingest, every exception swallowed and logged to local logger); acceptance: T032 + T034 pass
- [ ] T037 [US2] Implement `sdk/agentreplay/wrapper.py` `replay.wrap(client)`: intercepts OpenAI-compatible chat.completions.create, records verbatim request/response + latency/tokens as llm_call including HTTP-Referer/X-Title headers, redacting the Authorization header and any bearer token at the SDK boundary before buffering (FR-027), never alters the call or raises; acceptance: T033 passes including the no-Authorization-key assertion
- [ ] T038 [P] [US2] Implement `sdk/agentreplay/tool.py` `@replay.tool` (records name/args/result-or-error as tool_call) and `sdk/agentreplay/state.py` `record_state_change(from_state, to_state, trigger)` per contract payload shapes
- [ ] T039 [US2] Write `scripts/demo_agent.py`: minimal Nestaro-like conversation (system prompt, user Friday request, book_appointment tool, state changes) instrumented with the SDK, ending with `end_run()`, against the local stack; acceptance: run reaches status=completed and all steps visible in dashboard timeline with verbatim payloads (US2 AS-1/AS-3), then re-run with backend stopped — completes cleanly (AS-2)

**Checkpoint**: Live recording works end-to-end; invisibility guarantee proven

---

## Phase 5: User Story 3 - Sweep recorded runs for failures (Priority: P3)

**Goal**: The sweep is selective and safe across many runs: flags only
contradictory runs, leaves correct runs alone, skips in-flight runs,
supports run_ids subsets.

**Independent Test**: seed one contradictory + one correct + one running run;
sweep; only the contradictory run is flagged with a verdict.

### Tests for User Story 3 (write first, must fail) ⚠️

- [ ] T040 [P] [US3] Integration test in `tests/integration/test_sweep_selective.py`: sweep over {contradictory, correct, running, forked} seeds flags only the contradictory run (US3 AS-1/2); status=running and parent_run_id-set runs skipped without error; run_ids subset sweeps only listed runs; unparseable judge output → no verdict written, error reported

### Implementation for User Story 3

- [ ] T041 [US3] Extend `scripts/seed_demo_run.py` with a correct run (customer asks Friday, agent books friday) and a status=running run fixture
- [ ] T042 [US3] Harden sweep in `app/routers/detection.py`: candidate selection (all non-running, excluding forked runs with parent_run_id set, or explicit run_ids subset), per-run error isolation (one failure doesn't abort the sweep), no-garbage guarantee on parse failure; acceptance: T040 passes

**Checkpoint**: Detection is trustworthy across a pile of runs, not just the demo run

---

## Phase 6: User Story 4 - Fork safely: sandboxed tools, deterministic inference (Priority: P3)

**Goal**: Prove the fork safety contract holds for arbitrary forks: full
interception tier order, typed mock on divergence, temperature policy,
parent immutability. NOTE: Nestaro's single-shot fork path emits no tool
calls; the interceptor and these tests are retained deliberately as the
generality guarantee for tool-emitting agents (V2/roadmap) — do not delete
them as unused (research R4).

**Independent Test**: exercise the interceptor module directly against a
recorded run's tool_call steps to hit each interception tier; fork a run to
verify temperature policy and parent immutability; assert zero real tool
executions everywhere.

### Tests for User Story 4 (write first, must fail) ⚠️

- [ ] T043 [P] [US4] Unit tests in `tests/unit/test_canonical_json.py`: fixed vectors for canonical_json (key order, unicode, nesting) and sha256(name + canonical_json(args)) exact digests (research R3)
- [ ] T044 [P] [US4] Integration test in `tests/integration/test_interception_tiers.py`, driving `app/replay/interceptor.py` DIRECTLY against a seeded parent run's tool_call steps (not via the fork endpoint — Nestaro's single-shot forks emit no tool calls, research R4): (a) positional match by (run_id, seq) returns parent cached result; (b) seq mismatch but same name+args → hash fallback returns cached result; (c) unknown tool/args → typed mock {"result": {"mocked": true}, "error": null}; a sentinel real-tool spy proves zero real executions in all cases (US4 AS-1, constitution III)
- [ ] T045 [P] [US4] Integration test in `tests/integration/test_fork_safety.py`: forked llm_call.input records temperature 0 by default and the override value when given (US4 AS-2/3); full parent run+steps snapshot before fork == after fork (US4 AS-4, SC-005)

### Implementation for User Story 4

- [ ] T046 [US4] Harden `app/replay/interceptor.py` and `app/replay/engine.py` until T043–T045 pass without weakening tier order or immutability; document the no-real-tool invariant in module docstrings

**Checkpoint**: All four stories independently verified

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Delivery hygiene + final constitutional verification

- [ ] T047 [P] Create `ROADMAP.md` listing the seven NOT-in-V1 scope-guard items as roadmap entries (per docs/DECISIONS.md: "they go in ROADMAP.md, never in code")
- [ ] T048 [P] Write `README.md`: what AgentReplay is, architecture paragraph, link to specs/001-agentreplay-v1/quickstart.md, env var table, hackathon context
- [ ] T049 Clean-checkout validation of SC-008: fresh clone → `cp .env.example .env` + fill → `docker compose up` → full quickstart passes with three separate containers; fix any drift found (touching only non-test files)
- [ ] T050 Final constitution sweep: verify no scope-guard item crept into code (grep for otel/langchain/rate-limit/streaming/multi-tenant), pinned decisions hold (parent immutability, interception order, temp 0, verdict keys), pytest suite green; record results in PROGRESS.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational only (uses seeded fixture, not the SDK) — the MVP
- **US2 (Phase 4)**: Depends on Foundational (ingest API); reuses US1's timeline UI for its acceptance but SDK tasks themselves are independent
- **US3 (Phase 5)**: Depends on US1's detection core (T019–T022)
- **US4 (Phase 6)**: Depends on US1's fork engine (T024–T026)
- **Polish (Phase 7)**: Depends on all desired stories complete

### Within Each User Story

- Test tasks first; they MUST fail before the implementation task that makes them pass
- Analysis infra (T019–T021) before detection/analysis endpoints (T022–T023)
- Interceptor (T024) before engine (T025) before fork endpoint (T026)
- API client (T027) before dashboard pages (T028–T030)
- SDK buffer/transport (T036) before wrapper (T037)

### Parallel Opportunities

- Phase 1: T003, T004, T006 in parallel (after T001–T002 as noted)
- Phase 2: T011 ∥ T015 (different files); T012 tests written while T008–T010 land
- US1: T016–T018 tests in parallel; T019–T021 analysis modules in parallel; T027 in parallel with backend tasks
- US2: T032–T034 tests in parallel; T038 in parallel with T037
- US4: T043–T045 tests in parallel
- Polish: T047 ∥ T048

## Parallel Example: User Story 1

```bash
# Write all US1 tests together (must fail first):
Task: "Integration test detection sweep in tests/integration/test_detection.py"
Task: "Integration test analysis verdict in tests/integration/test_analysis.py"
Task: "Integration test fork safety in tests/integration/test_fork.py"

# Then build analysis infra together:
Task: "OpenAI-compatible client in app/analysis/client.py"
Task: "Run serializer in app/analysis/serializer.py"
Task: "Strict-JSON prompts in app/analysis/prompts.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup (T001–T007) → compose stack up
2. Phase 2: Foundational (T008–T015) → seeded run readable
3. Phase 3: US1 (T016–T031) → **the demo** (detect → analyze → fork → compare)
4. **STOP and VALIDATE**: T031 is the hackathon demo gate (SC-001)

### Incremental Delivery

1. Setup + Foundational → ingest/read working
2. US1 → MVP demo (judges could see this alone)
3. US2 → live SDK recording ("it's real, not a fixture")
4. US3 → detection at scale credibility
5. US4 → safety-contract proof
6. Polish → clean-checkout SC-008 + roadmap story

### Solo Builder Note

One task per session (session rule 1). The task order above is already a
valid sequential schedule; [P] markers matter for batching within a day, not
for parallel staffing.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to spec.md user stories US1–US4
- Verify tests fail before implementing; implementation sessions never edit `tests/`
- Commit after each task: `T-NN: <what>`; append one line to PROGRESS.md
- The pinned decisions (constitution I–VII) are the tiebreaker for any ambiguity — stop and ask rather than guess
