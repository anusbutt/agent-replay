# PROGRESS.md — running log

One line per completed task, appended by each session. Newest at the bottom.
Format: `T-NN done: <one-line summary> | blocked: <none or what>`

Also note here any decision made mid-build that isn't yet reflected in
docs/DECISIONS.md or docs/DATA_CONTRACT.md, so the next session sees it.

---

<!-- entries start below -->

## Session 2026-07-04 → 2026-07-06 — SDD artifacts (no build tasks executed yet)

Planning/spec session. No T-NN tasks from tasks.md executed; implementation
starts next session at T001. Branch: `001-agentreplay-v1`.

- Constitution ratified at `.specify/memory/constitution.md` v1.1.0 —
  principles I–VI transcribe docs/DECISIONS.md pinned decisions 1–6;
  principle VII = Docker containerization (mirrored into DECISIONS.md as
  pinned decision 7: three compose services backend/frontend/db, one image
  per service, `docker compose up`, never a monster image).
- Spec + plan + research + data-model + contracts/api.openapi.yaml +
  quickstart + tasks.md (50 tasks, 7 phases, US1 = Friday/Saturday MVP)
  all generated under `specs/001-agentreplay-v1/`.
- /sp.analyze ran: 9 findings (0 critical), all 9 fixed — incl. ingest never
  downgrades `flagged` / never clobbers verdict keys (T013); SDK `end_run()`
  added (T035); sweep excludes forks; detection sets `flagged` (not failed).
- docs/DATA_CONTRACT.md was amended mid-session from Nestaro's real payload
  (history user message in position, HTTP-Referer/X-Title headers recorded,
  NEVER record Authorization, tools are NOT LLM-native). All artifacts
  re-synced byte-identical; verified 5/5 JSON blocks + 43/43 payload lines
  in spec.md and data-model.md. New FR-027 = Authorization redaction at SDK
  boundary (test assertion in T033, acceptance in T037).
- DECISION settled by maintainer 2026-07-06, recorded in research R4 /
  spec FR-015 but NOT YET in docs/DECISIONS.md (candidate pinned decision 8):
  **single-shot fork** — a fork executes exactly ONE live llm_call at the
  fork step (temp 0, single stored step at seq 1, agent_id/session_id copied
  from parent); no walking parent steps, no history-format reconstruction,
  no agent code re-execution. CompareView proof = flipped decision
  (saturday → friday); fork never re-books. Interceptor (pinned decision 3)
  kept + tested in isolation as generality guarantee — do NOT delete as
  unused.
- PHRs 0001–0006 under history/prompts/ (constitution/ + 001-agentreplay-v1/).
- Next session: /sp.implement — execute T001 ONLY (one task per session),
  then check its box in tasks.md and append a T-NN line here.

blocked: none

## Session 2026-07-07 — Phase 1: Setup (T001–T007) — maintainer-directed phase batch

Maintainer authorized phase-by-phase execution (supersedes one-task-per-session
for this engagement): implement a full phase, stop, report for validation.

- T-01 done: project skeleton (app/{routers,replay,analysis} + __init__.py, sdk/agentreplay, dashboard, tests/{contract,integration,unit}, scripts) | blocked: none
- T-02 done: pyproject.toml (fastapi/sqlmodel/httpx/psycopg/uvicorn + pytest/respx dev) + app/main.py GET /health → {"ok": true}, verified via uvicorn + curl | blocked: none
- T-03 done: Next.js 16 + TS + Tailwind 4 scaffold in dashboard/ (create-next-app, no extra UI libs); `npm run dev` served placeholder (title "Create Next App") | blocked: none
- T-04 done: .env.example with DATABASE_URL, AGENTREPLAY_API_KEY, ANALYSIS_BASE_URL/KEY, REPLAY_BASE_URL/KEY — no real values | blocked: none
- T-05 done: root Dockerfile (python:3.11-slim, dev deps + tests/ + scripts/ included for in-container pytest, uvicorn :8000, env-only config) | blocked: none
- T-06 done: dashboard/Dockerfile (node:24-alpine two-stage build → next start :3000) + dashboard/.dockerignore | blocked: none
- T-07 done: compose.yml — three services backend/frontend/db (postgres:16 + named volume + healthcheck); `docker compose up -d` verified: all three running, backend /health {"ok":true}, frontend serves page | blocked: none

Environment notes (WSL2 host, repo on /mnt/c):
- docker compose plugin (v5.3.1) and buildx (v0.19.3) installed user-level to
  ~/.docker/cli-plugins — host had docker 29 but no compose and buildx 0.12.
- npm on /mnt/c (DrvFs) failed to create node_modules/.bin symlinks on first
  scaffold and hit ENOTEMPTY on reinstall; fixed by clean node_modules
  reinstall. package-lock.json initially generated with --package-lock-only
  was incomplete (missing @babel/core subtree + platform optional deps) →
  `npm ci` failed in image builds; fixed by deleting and regenerating the
  lockfile from scratch inside node:24-alpine (same image as the Dockerfile,
  which was bumped node:22→node:24 to match). LOCKFILE_SYNC_OK verified.
- .gitignore and .dockerignore (root + dashboard) created per implement flow.

blocked: none — awaiting maintainer validation before Phase 2 (T008–T015)

## Session 2026-07-07 (later) — Phase 2: Foundational (T008–T015)

- T-08 done: SQLModel Run+Step in app/models.py — enums byte-identical, JSONB columns, UNIQUE (run_id, seq), indexes on agent_id/session_id/run_id | blocked: none
- T-09 done: app/db.py engine/session from DATABASE_URL + create_all wired into main.py lifespan | blocked: none
- T-10 done: static Bearer-key auth dependency (compare_digest) applied to all routers via include_router; /health stays open | blocked: none
- T-11 done: app/schemas.py — IngestBatch/IngestResult/RunOut/StepOut/RunDetail/ForkRequest/AnalysisVerdict/DetectionVerdict/SweepResult/Error per openapi contract | blocked: none
- T-12 done: contract tests tests/contract/{test_ingest,test_runs}.py + tests/conftest.py — verified FAILING first (7 failed) before implementation | blocked: none
- T-13 done: POST /ingest — run upsert (flagged never downgraded; detection/analysis keys never clobbered), insert-only steps, per-item rejection; ingest tests pass | blocked: none
- T-14 done: GET /runs (agent_id/session_id/status/limit/offset) + GET /runs/{id} steps ordered by seq; runs tests pass | blocked: none
- T-15 done: scripts/seed_demo_run.py — Nestaro Friday/Saturday fixture (5 steps, verbatim contract shapes, no Authorization key) seeded; accepted=5, visible via GET /runs | blocked: none

Verification: 8/8 contract tests pass on host venv AND inside backend container
(docker compose exec backend pytest). Demo run 11111111-1111-4111-8111-111111111111
seeded against rebuilt backend container.

blocked: none — awaiting maintainer validation before Phase 3 (US1, T016–T031)

## Session 2026-07-08 — Phase 3: US1 MVP (T016–T030 done; T031 deferred)

- T-16 done: tests/integration/test_detection.py — respx-stubbed sweep flags contradictory run + writes detection verdict; unparseable model output writes nothing (SweepResult.detection=None, error set) | blocked: none
- T-17 done: tests/integration/test_analysis.py — respx-stubbed analyze stores {failing_step,root_cause,suggested_fix}; 502 + run unchanged on model failure | blocked: none
- T-18 done: tests/integration/test_fork.py — respx-stubbed fork creates new run (parent_run_id+fork_step, single llm_call seq 1, temp 0 default + override), parent byte-identical before/after, 422 on no reconstructable llm_call context | blocked: none
- T-19 done: app/analysis/client.py — OpenAI-compatible chat_completion() on ANALYSIS_BASE_URL/ANALYSIS_API_KEY | blocked: none
- T-20 done: app/analysis/serializer.py — steps -> compact transcript for judge prompts | blocked: none
- T-21 done: app/analysis/prompts.py — strict-JSON detection/analysis prompts + defensive extract_json_object() | blocked: none
- T-22 done: POST /detect/sweep in app/routers/detection.py — candidate selection (skip running/forked), verdict merge, flagged on fail, per-run error isolation | blocked: none
- T-23 done: POST /runs/{id}/analyze in app/routers/analysis.py — 502 + unchanged run on model/parse failure | blocked: none
- T-24 done: app/replay/interceptor.py — canonical_json + sha256 hash, positional -> hash -> typed mock resolution order, no code path to real tool execution | blocked: none
- T-25 done: app/replay/engine.py — single-shot fork: nearest llm_call at-or-before fork_step, system_prompt modification, ONE live call via REPLAY_BASE_URL at temp 0 (override honored), fork run marked completed/failed | blocked: none
- T-26 done: POST /runs/{id}/fork in app/routers/fork.py — 422 + no fork row when no reconstructable llm_call context | blocked: none
- T-27 done: dashboard/src/lib/api.ts — typed client for all 5 endpoints, types mirroring openapi contract | blocked: none
- T-28 done: dashboard/src/app/page.tsx — runs list with status badges, fork lineage indicator | blocked: none
- T-29 done: dashboard/src/app/runs/[id]/page.tsx + TimelineStep.tsx + VerdictBadge.tsx — seq-ordered expandable timeline, detection/analysis verdict cards | blocked: none
- T-30 done: ForkPanel.tsx (prefilled system prompt + suggested_fix) + CompareView.tsx (parent-labeled step-K + subsequent tool_calls vs fork's single step) wired into run detail page | blocked: none

Verification: 16/16 backend tests pass on host venv AND in-container
(docker compose exec backend pytest). `npm run build` compiles clean
(TypeScript, no errors). Manual UI verification performed with a throwaway
local mock OpenAI-compatible server (NOT part of the deliverable) standing in
for ANALYSIS_BASE_URL/REPLAY_BASE_URL — confirmed via rendered HTML that the
runs list, timeline, detection/analysis verdict cards, and fork+CompareView
all render correctly against real HTTP round-trips through the actual
backend code and a real Postgres row.

Bugs found and fixed during this phase (all in code/tests authored THIS
phase, none in pre-existing tests):
1. tests/integration/test_fork.py — session_id collision caused false
   positive on re-run (test-isolation bug in my own new test); fixed with a
   per-invocation unique session_id.
2. dashboard/src/lib/api.ts + compose.yml — frontend container returned
   HTTP 500 on every page: Server Components run inside the frontend
   container where `localhost:8000` resolves to itself, not the backend
   container. Fixed by adding a server-only `API_BASE_URL_INTERNAL` env var
   (Docker network hostname `http://backend:8000`) used only when
   `typeof window === "undefined"`, while client-side calls keep using the
   build-time `NEXT_PUBLIC_API_BASE_URL`. Also required `NODE_OPTIONS=
   --dns-result-order=ipv4first` (Node/undici IPv6-first fetch bug on the
   Docker bridge network) and a `--no-cache` rebuild — a cached image layer
   was silently serving stale code after a normal `--build`.
3. tests/integration/test_{detection,analysis,fork}.py — the ANALYSIS_/
   REPLAY_BASE_URL env-var helpers used `os.environ.setdefault(...)`, which
   is a no-op when the container already sets the var (even to "" via
   compose's `${VAR:-}` default) — desyncing the respx mock target from what
   the app actually calls. Fixed by force-setting the env var instead of
   defaulting. Caused 2 false failures when run in-container (passed on host
   where the var was truly unset) — root-caused and fixed, not skipped.
4. Deleted ~105 runs of test-created data that had accumulated in the shared
   compose `db` volume under agent_id="nestaro"/"nestaro-test" (host pytest
   runs share the same Postgres as the demo seed by design — no separate
   test DB in V1). Kept only the one real seeded demo run
   (11111111-1111-4111-8111-111111111111) so the dashboard/T031 demo isn't
   cluttered.

T-031 NOT done: requires real ANALYSIS_BASE_URL/ANALYSIS_API_KEY (Gemma on
AMD MI300X vLLM or Fireworks fallback) and REPLAY_BASE_URL/REPLAY_API_KEY
(OpenRouter) — maintainer confirmed these aren't ready yet; deferred by
maintainer decision, to be run once credentials are available.

blocked: T-031 blocked on real ANALYSIS_BASE_URL/REPLAY_BASE_URL credentials

## Session 2026-07-09 — T031: real end-to-end SC-001 demo (Phase 3 complete)

Ran quickstart.md steps 1–6 against the live containerized compose stack
(backend/frontend/db all `docker compose ps` = running) with REAL inference:
ANALYSIS_BASE_URL=REPLAY_BASE_URL=https://openrouter.ai/api/v1 (maintainer's
OpenRouter key, confirmed via AskUserQuestion to reuse for both analysis and
fork since no separate Gemma/MI300X or Fireworks endpoint was available).
Analysis model bumped from a guessed `google/gemma-3-27b-it` to the verified-
available `google/gemma-4-31b-it` (queried OpenRouter's live /models catalog
— exact "Gemma 4" match per spec). Fork calls reuse the recorded model id
`deepseek/deepseek-chat` (also verified present on OpenRouter), per research
R6.

**Fixture bug found and fixed**: the first sweep attempt returned
`verdict: "pass"` from the real judge — scripts/seed_demo_run.py's original
fixture had a later customer turn ("ok sure, book it") plus a state_change
`trigger: "user_confirmed"` that genuinely read as the customer consenting to
Saturday, undermining the intended contradiction. This was a legitimate
judgment by the real model, not a bug in the judge. Fixed by removing the
consenting follow-up turn and renaming the trigger to `agent_selected_slot`
(the agent proceeded to book without the customer ever confirming Saturday
specifically) — re-seeded (deleted+re-ingested the fixed UUID run) and the
sweep then correctly flagged it.

**Evidence** (real inference, no stubs):

- Demo run: `11111111-1111-4111-8111-111111111111` (agent_id=nestaro,
  session_id=fbm-24601), 4 steps: state_change → llm_call (seq 2, FAILING) →
  state_change → tool_call (books saturday 14:00).
- `POST /detect/sweep` → `{"verdict": "fail", "reason": "The user explicitly
  requested duct cleaning for Friday, but the agent booked the appointment
  for Saturday.", "contradiction": {"user_intent": "duct cleaning Friday",
  "agent_action": "booked Saturday at 2:00 PM"}}`; run status → `flagged`.
- `POST /runs/{id}/analyze` → `{"failing_step": 2, "root_cause": "The agent
  ignored the user's explicit request for Friday and unilaterally booked a
  Saturday slot based on the system prompt's preference for efficiency,
  violating user intent.", "suggested_fix": "Add to system prompt: 'While you
  should prefer offering Saturday slots to keep the schedule efficient, you
  must always prioritize and honor the specific day requested by the
  customer if they provide one.'"}` — failing_step 2 exists in the run
  (matches the seq-2 llm_call) — SC-007 satisfied.
- `POST /runs/{id}/fork` with the suggested fix applied to the system prompt,
  fork_step=2 → fork run `b767d013-6c22-4e7a-ae45-c55e36d6c033`
  (parent_run_id=demo run, fork_step=2, agent_id/session_id copied from
  parent), exactly ONE stored step (seq 1, llm_call, temperature=0 recorded
  in input), zero tool_call steps. Live model reply: **"Perfect! I can book
  you for this Friday. We have morning or afternoon slots available—which
  works best for you?"** — the decision flipped Saturday → Friday. SC-001
  proof achieved with real inference (not a stub).
- Parent immutability (SC-005) verified after the fork: parent run status
  still `flagged`, still exactly 4 steps, detection/analysis verdicts intact
  and unchanged.
- Dashboard CompareView (http://localhost:3000/runs/b767d013-...) confirmed
  via rendered HTML: parent-labeled step-2 text ("...locked in Saturday at
  2:00 PM...") and the parent's subsequent tool_call (book_appointment
  day=saturday, labeled parent-origin) shown alongside the fork's Friday
  reply, with "No tool call — the fork never re-books anything" — FR-012
  satisfied.
- Zero real tool executions across the fork (SC-004): fork run has exactly
  one step, type llm_call, no tool_call steps present.

SC-001 through SC-005, SC-006, SC-007 all verified against the live
containerized stack with real model inference. SC-008 (docker compose up
from clean checkout) was verified structurally in Phase 1; full clean-clone
re-verification remains Phase 7 polish (T049).

blocked: none — Phase 3 (US1, the MVP) is fully complete, T016–T031 all done.

## Session 2026-07-09 (cont'd) — Phase 4: US2 SDK (T032–T039, all done)

- T-32 done: tests/unit/test_sdk_buffer.py — contiguous 1-based seq, IngestBatch shape, drain semantics | blocked: none
- T-33 done: tests/unit/test_sdk_wrapper.py — verbatim llm_call recording (incl. history message in position, headers), latency/tokens populated, no-Authorization-key-at-any-level assertion | blocked: none
- T-34 done: tests/integration/test_sdk_never_raises.py — dead port + respx-mocked 500 server + pre-init no-op, all complete without raising | blocked: none
- T-35 done: sdk/agentreplay/__init__.py — init/wrap/tool/record_state_change/flush/end_run public API, module-level _state singleton, AUTO_FLUSH_THRESHOLD=10; sdk/pyproject.toml (httpx only runtime dep) | blocked: none
- T-36 done: sdk/agentreplay/buffer.py (seq assignment, IngestBatch shaping) + transport.py (httpx POST /ingest, every exception + non-2xx response swallowed and logged) | blocked: none
- T-37 done: sdk/agentreplay/wrapper.py — replay.wrap(client) records verbatim request/response via duck-typed .model_dump()/.to_dict(), recursive Authorization redaction at any nesting depth (FR-027), real call behavior never altered | blocked: none
- T-38 done: sdk/agentreplay/tool.py (@replay.tool, inspect.signature-bound args) + state.py (record_state_change) | blocked: none
- T-39 done: scripts/demo_agent.py — minimal hand-rolled OpenAI-compatible client (httpx only, no `openai` dependency, proves wrap() is duck-typed-generic), real conversation against OpenRouter, instrumented end-to-end, ends with end_run() | blocked: none

Design decision (not pre-specified, resolved during implementation): the SDK
buffers every event in memory (no network) and only performs actual network
I/O synchronously inside flush() (auto-triggered at AUTO_FLUSH_THRESHOLD=10
buffered steps, or explicitly via flush()/end_run()) — chosen over a
background-thread/async-fire-and-forget design for determinism and
testability (T034's dead-port/erroring-server assertions are flake-free),
while still satisfying "buffer in memory, deliver in batches, errors never
propagate" (FR-004/FR-005). Documented inline in transport.py/buffer.py.

**Verification — T039 acceptance, run against the LIVE containerized stack
with real OpenRouter inference (same key as T031)**:
- AS-1/AS-3: `python scripts/demo_agent.py` (PYTHONPATH=sdk) → real LLM
  reply ("Got it! Let's book your duct cleaning for Friday...") + real tool
  booking; run `690be766-fb5b-4d74-a33c-a35ebf432888` reached
  `status=completed`, all 4 steps (state_change, llm_call, state_change,
  tool_call) visible via GET /runs/{id} in seq order, llm_call.input/output
  verbatim (including full OpenRouter usage/cost breakdown), tokens_in=47/
  tokens_out=25 populated, zero "Authorization" key anywhere in input.
- AS-2: `docker compose stop backend` → re-ran demo_agent.py → exit code 0,
  the real LLM call and tool still completed normally, only a locally-logged
  warning ("agentreplay: failed to deliver batch: [Errno 111] Connection
  refused") — no exception surfaced to the host script. Backend restarted
  and confirmed healthy afterward.

26/26 tests pass (16 backend + 10 SDK), host venv. Cleaned test-polluted db
rows (host pytest reruns during SDK work) three more times this session,
keeping only: the T031 demo pair + the one real demo_agent run, as evidence.

**Phase 4 checkpoint met: live recording works end-to-end; invisibility
guarantee proven with a real backend outage, not just a mock.**

blocked: none — Phase 4 (US2) complete. Next: Phase 5 (US3, detection at
scale, T040–T042) or Phase 6 (US4, fork safety proof, T043–T046).

## Session 2026-07-09 (cont'd) — Phase 5: US3 sweep at scale (T040–T042, all done)

- T-40 done: tests/integration/test_sweep_selective.py — 4 tests: default sweep flags only contradictory + skips running/forked; explicit run_ids can target running/forked (openapi "OR the given run_ids" semantics); run_ids subset scopes correctly; one run's judge failure doesn't abort the sweep for others | blocked: none
- T-41 done: scripts/seed_demo_run.py extended with CORRECT_RUN_ID (Friday asked, Friday booked — no contradiction) and RUNNING_RUN_ID (status=running, no ended_at, mid-conversation) fixtures, POSTed alongside the original contradictory demo run | blocked: none
- T-42 done: app/routers/detection.py's candidate selection, per-run error isolation, and no-garbage guarantee were ALREADY correct from Phase 3 (T022) — T040's tests confirm this with zero detection.py code changes needed; only the query_judge retry (already added post-Phase-4 as a bugfix) benefits both endpoints | blocked: none

**Real infrastructure fix (not a task, but required to get here)**: T040's
"one run's judge failure doesn't abort the sweep" test exposed that
tests/conftest.py shared the SAME Postgres database as the demo/T031/T039
evidence — a recurring pollution problem flagged three times already this
session, now escalated from cosmetic clutter into an actual test-correctness
bug (a parameterless sweep picked up leftover runs from every prior pytest
invocation this session, breaking a call-count assertion). Fixed properly:
tests/conftest.py now forces pytest onto a separate `<dbname>_test` database
(auto-created via a maintenance-db CREATE DATABASE, idempotent), truncated
at the start of every test session — isolating tests from the demo dataset
permanently, on both host venv AND in-container. Also found and fixed: the
backend Dockerfile never COPYd sdk/ into the image, so the SDK unit/
integration tests (Phase 4) had NEVER actually run in-container — fixed
(`COPY sdk ./sdk`) and verified: 30/30 tests now pass identically on host
and in-container. (Also had to `--no-cache` both rebuilds — Docker's build
cache silently served stale layers again, third time this project has hit
that exact failure mode with `--build` alone.)

**Real-world verification** (not just tests — live seeded runs, real
inference, same OpenRouter key as T031/T039): ran scripts/seed_demo_run.py
against the live stack (idempotent re-seed of the contradictory run +
fresh correct/running fixtures), then POST /detect/sweep with real Gemma-4:
- correct run (44444444...) -> verdict "pass", stays completed
- demo_agent's own real run (690be766..., from T039) -> verdict "pass",
  stays completed (bonus cross-check — a real recorded run with no
  contradiction correctly passes too)
- contradictory run (11111111...) -> verdict "fail", flagged
- running run (55555555...) -> absent from results entirely, untouched
  (status still running, no detection key written)
- fork run (b767d013...) -> absent from results entirely, untouched by
  THIS sweep (a stray "detection: pass" key from an earlier manual
  dashboard click — made before the fork-actions-hidden UX fix — was found
  and cleaned up; not caused by current code)

This is exactly US3's independent test scenario ("seed one contradictory +
one correct + one running run; sweep; only the contradictory run is flagged
with a verdict"), proven against the live containerized stack with real
model inference, not stubs.

30/30 tests pass (26 backend/SDK + 4 new sweep-selectivity), host AND
in-container, confirmed stable across repeated invocations without manual
cleanup for the first time this project.

blocked: none — Phase 5 (US3) complete. Next: Phase 6 (US4 — fork safety
proof via the interceptor, T043–T046) or Phase 7 (polish, T047–T050).

## Session 2026-07-09 (cont'd) — Phase 6: US4 fork safety proof (T043–T046, all done)

- T-43 done: tests/unit/test_canonical_json.py — fixed vectors (key order, unicode preserved unescaped, nested/list order, book_appointment example), sha256 digests hardcoded and verified byte-exact, key-order-independence and content-sensitivity assertions | blocked: none
- T-44 done: tests/integration/test_interception_tiers.py — drives app/replay/interceptor.py DIRECTLY against real DB-persisted Step rows (not via /fork): positional match, hash fallback (incl. dict-key-reordering insensitivity), typed mock on unknown tool, (run_id,seq) scoping doesn't leak across runs, sentinel real-tool spy proves zero real executions across every tier (US4 AS-1) | blocked: none
- T-45 done: tests/integration/test_fork_safety.py — dedicated US4 file (deliberately overlapping test_fork.py per research R4): temperature 0 default, override honored across multiple values, parent run+steps byte-for-byte unchanged across 3 repeated forks off the same parent, fork never produces a tool_call step | blocked: none
- T-46 done: app/replay/interceptor.py + engine.py needed ZERO code changes — 18/18 new US4 tests passed against the Phase 3 (T024/T025) implementation on the first run; the no-real-tool invariant was already documented in both module docstrings from Phase 3

Third phase in a row (after Phase 5's T042) where the "harden until tests
pass" task required no implementation changes — Phase 3's interceptor/engine
were built correctly the first time against the constitution's exact tier
order and immutability requirements.

48/48 tests pass (30 prior + 18 new), host AND in-container (re-verified
new test files actually landed in the rebuilt image this time, after
Phase 5's stale-cache lesson — `docker compose exec backend ls` on all
three new files before trusting the container pytest run). Demo db
confirmed still exactly 5 legitimate rows after both host and in-container
runs — the Phase 5 test-isolation fix is holding with zero manual cleanup
needed for the first time across a full phase.

blocked: none — Phase 6 (US4) complete. All four user stories (US1-US4)
now done. Remaining: Phase 7 — Polish & Cross-Cutting Concerns (T047-T050):
ROADMAP.md, README.md, clean-checkout SC-008 validation, final constitution
sweep.
