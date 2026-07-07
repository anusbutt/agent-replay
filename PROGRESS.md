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
