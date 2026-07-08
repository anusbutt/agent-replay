---
id: 0011
title: Implement Phase 3 US1 MVP
stage: green
date: 2026-07-08
surface: agent
model: claude-sonnet-5
feature: 001-agentreplay-v1
branch: 001-agentreplay-v1
user: anusbutt
command: /sp.implement
labels: ["phase-3", "us1", "detection", "analysis", "fork-engine", "dashboard", "tdd", "docker-networking"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - tests/integration/test_detection.py
 - tests/integration/test_analysis.py
 - tests/integration/test_fork.py
 - app/analysis/client.py
 - app/analysis/serializer.py
 - app/analysis/prompts.py
 - app/routers/detection.py
 - app/routers/analysis.py
 - app/routers/fork.py
 - app/replay/interceptor.py
 - app/replay/engine.py
 - app/schemas.py
 - app/main.py
 - dashboard/src/lib/api.ts
 - dashboard/src/app/page.tsx
 - dashboard/src/app/runs/[id]/page.tsx
 - dashboard/src/components/TimelineStep.tsx
 - dashboard/src/components/VerdictBadge.tsx
 - dashboard/src/components/RunActions.tsx
 - dashboard/src/components/ForkPanel.tsx
 - dashboard/src/components/CompareView.tsx
 - compose.yml
 - dashboard/Dockerfile
 - specs/001-agentreplay-v1/tasks.md
 - PROGRESS.md
tests:
 - tests/integration/test_detection.py (2 tests)
 - tests/integration/test_analysis.py (3 tests)
 - tests/integration/test_fork.py (3 tests)
 - full suite: 16/16 passing, host venv and in-container
---

## Prompt

phase 2 validated, start phase 3

(Standing maintainer rules from session start: implement phase by phase,
stop after every phase for validation, summarize what was done, list all
files created/updated. Mid-phase the maintainer asked to verify the
dashboard by running `npm run dev` natively on Windows — cmd.exe, not
WSL/PowerShell — after WSL's cross-platform lightningcss binary resolution
proved unreliable. After manual verification the maintainer asked "is that
data faked?" and, given the answer, chose via AskUserQuestion to defer T031
(the real end-to-end demo needing live ANALYSIS_BASE_URL/REPLAY_BASE_URL
credentials) and proceed straight to Phase 3 bookkeeping.)

## Response snapshot

Executed Phase 3 US1 (T016–T030) in tasks.md order with TDD: wrote and
verified-failing 3 integration test files (detection sweep, analyze,
fork — respx-stubbed), then implemented analysis infra (client/serializer/
prompts), detection sweep and analyze endpoints, the tool interceptor
(canonical_json + sha256, positional→hash→typed-mock), the single-shot
replay engine (research R4: nearest llm_call at-or-before fork_step,
system_prompt modification, exactly ONE live call at temp 0 unless
overridden), the fork endpoint, and the full dashboard (typed API client,
runs list, run detail with timeline + verdict cards, fork panel + compare
view). 16/16 backend tests pass host+container.

During manual UI verification (spun up a throwaway, uncommitted mock
OpenAI-compatible server since no real ANALYSIS_BASE_URL/REPLAY_BASE_URL
were available) found and fixed three real bugs, all in code/tests authored
this same phase: (1) a test-isolation bug in test_fork.py (hardcoded
session_id colliding across runs); (2) the frontend container 500'd on every
page because Server Components run inside the frontend container where
"localhost:8000" resolves to itself, not backend — fixed with a
server-only API_BASE_URL_INTERNAL env var read only when
typeof window === "undefined", plus a Node/undici IPv6-first fetch bug
requiring NODE_OPTIONS=--dns-result-order=ipv4first, plus discovering a
`--build` had silently served a stale cached layer (needed --no-cache to
actually pick up the fix); (3) test env-var helpers used
os.environ.setdefault(...), a no-op when the container already set the var
(even to "" via compose's ${VAR:-} default), desyncing respx mock targets
from what the app actually called — 2 false failures in-container, fixed by
force-setting. Also cleaned ~105 test-polluted rows out of the shared
compose db volume (host pytest runs share the same Postgres as the demo
seed by design), keeping only the one real seeded run.

T031 (the real SC-001 demo against live ANALYSIS_BASE_URL/REPLAY_BASE_URL)
is explicitly deferred per maintainer decision — not done, not faked as done.

## Outcome

- ✅ Impact: US1 (detect → analyze → fork → compare) fully implemented and wired end-to-end; only the real-model demo run (T031) remains, blocked on credentials.
- 🧪 Tests: 16/16 backend tests pass (host venv + in-container); dashboard `npm run build` compiles clean; manual UI verification confirmed real HTTP round-trips render correctly (mock LLM responses, not real model output).
- 📁 Files: 21 files created/modified across app/analysis, app/routers, app/replay, dashboard/src, plus compose.yml and dashboard/Dockerfile bugfixes; tasks.md T016–T030 ticked; PROGRESS.md appended with full bug/fix trail.
- 🔁 Next prompts: obtain real ANALYSIS_BASE_URL/ANALYSIS_API_KEY (Gemma/MI300X or Fireworks) and REPLAY_BASE_URL/REPLAY_API_KEY (OpenRouter) → run T031 → Phase 4 (US2, SDK).
- 🧠 Reflection: the SSR-vs-browser API base URL split is a real, non-obvious Next.js-in-Docker gotcha (would recur for any future server-rendered page hitting the backend) — worth remembering for the SDK/demo-agent work in Phase 4, which will also run inside or alongside containers.

## Evaluation notes (flywheel)

- Failure modes observed: Docker `--build` silently reused a stale cached layer despite source changes (needed --no-cache to force); Node/undici IPv6-first DNS resolution failing silently on Docker bridge networks; shared test/dev database causing test-data pollution.
- Graders run and results (PASS/FAIL): pytest full suite PASS (16/16) host and container; `npm run build` PASS (TypeScript clean); manual curl-of-rendered-HTML verification PASS for runs list, timeline, verdict cards, compare view.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): consider a separate test-only DATABASE_URL to stop future pytest runs from polluting the demo dataset.
