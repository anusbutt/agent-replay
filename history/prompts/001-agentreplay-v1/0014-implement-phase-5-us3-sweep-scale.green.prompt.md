---
id: 0014
title: Implement Phase 5 US3 sweep scale
stage: green
date: 2026-07-09
surface: agent
model: claude-sonnet-5
feature: 001-agentreplay-v1
branch: 001-agentreplay-v1
user: anusbutt
command: /sp.implement
labels: ["phase-5", "us3", "sweep", "test-isolation", "docker-cache-bug"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - tests/integration/test_sweep_selective.py
 - tests/conftest.py
 - Dockerfile
 - scripts/seed_demo_run.py
 - specs/001-agentreplay-v1/tasks.md
 - PROGRESS.md
tests:
 - tests/integration/test_sweep_selective.py (4 tests)
 - full suite 30/30 passing, host AND in-container (first time both fully verified)
---

## Prompt

analyze works now, start phase 5.

(Preceded by two live bug reports and fixes this session: CORS blocking
client-side fetch calls, and a fork-run Analyze click producing a null
failing_step pydantic error — both fixed and committed before this phase
began. Standing maintainer rules: phase-by-phase, stop for validation,
summarize + list files every time.)

## Response snapshot

Read Phase 5's tasks (T040-T042) and found T042's implementation
(candidate selection excluding running/forked runs by default, explicit
run_ids bypass per openapi's "OR the given run_ids", per-run error
isolation, no-garbage guarantee) was ALREADY fully correct from Phase 3 —
wrote T040's test file first and 3/4 tests passed immediately against the
existing detection.py with zero changes.

The 4th test (one judge failure shouldn't abort the sweep for others)
exposed a real bug: 35 mock calls instead of the expected 2, because
tests/conftest.py shared the SAME Postgres database as the demo/T031/T039
evidence — every host pytest invocation this session had been leaving
dozens of runs behind, and a parameterless sweep picked all of them up as
candidates. This had been flagged as cosmetic pollution three times already
in PROGRESS.md; this time it broke an actual assertion, so fixed it
properly rather than patching around it again: conftest.py now forces
pytest onto an isolated <dbname>_test database (auto-created via a
maintenance-db connection, truncated at session start). Verifying this
in-container surfaced a SECOND real bug: the Dockerfile never copied sdk/
into the image, so Phase 4's SDK tests had literally never run in-container
at all — fixed with a COPY line. Both fixes needed --no-cache to actually
take effect; docker compose build --build alone silently served stale
layers again (the third time this exact failure mode has hit this project).
After both fixes: 30/30 pass identically on host and in-container,
repeatable across multiple invocations without manual cleanup for the
first time.

Extended scripts/seed_demo_run.py (T041) with a correct-run and a
running-run fixture, ran it against the live stack (idempotent re-seed),
then ran POST /detect/sweep with real Gemma-4 inference: correct run and
demo_agent's own real run both correctly passed; contradictory run
correctly flagged; running and forked runs correctly absent from results
entirely — proving US3's independent test scenario for real, not just via
mocks. Found and cleaned a stray leftover "detection: pass" key on the fork
run (residue from the maintainer's own manual dashboard click before the
fork-actions-hidden UX fix landed — not caused by current code).

## Outcome

- ✅ Impact: US3 (detection at scale) proven both via tests and live real-inference verification; the recurring test/demo-database pollution problem — flagged three times, never properly fixed — is now permanently resolved. Phase 5 complete.
- 🧪 Tests: 4/4 new sweep-selectivity tests pass; full suite 30/30, confirmed passing on BOTH host venv and in-container for the first time (previous phases' SDK tests had silently never run in-container).
- 📁 Files: 1 test file created; conftest.py, Dockerfile, seed_demo_run.py modified; tasks.md/PROGRESS.md updated. 4 commits (T-40, infra fix, T-41, bookkeeping).
- 🔁 Next prompts: Phase 6 (US4 — fork safety proof, T043–T046) or Phase 7 (polish: README, ROADMAP.md, clean-checkout SC-008 validation, T047–T050).
- 🧠 Reflection: three "flag and move on" notes about the same pollution issue in a row should have triggered fixing it the first time it was noticed, not the third time it caused an actual failure — a pattern worth recognizing sooner: recurring flagged-but-deferred issues are a signal to stop and fix, not to flag a fourth time.

## Evaluation notes (flywheel)

- Failure modes observed: shared test/dev database causing a real assertion failure (not just clutter); Docker build cache serving stale layers under `--build` alone for the third time this project (backend Dockerfile change, frontend Dockerfile change earlier, now backend again) — this is a pattern worth remembering: always verify with a content check (grep the built image), not just a successful exit code, after any Dockerfile change.
- Graders run and results (PASS/FAIL): pytest full suite PASS (30/30) host and container; live sweep against real seeded runs with real inference PASS (matches US3's stated independent test exactly).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): none outstanding for this area — the recurring db-pollution and Docker-cache issues are now both resolved with durable fixes, not just workarounds.
