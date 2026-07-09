---
id: 0013
title: Implement Phase 4 US2 SDK
stage: green
date: 2026-07-09
surface: agent
model: claude-sonnet-5
feature: 001-agentreplay-v1
branch: 001-agentreplay-v1
user: anusbutt
command: /sp.implement
labels: ["phase-4", "us2", "sdk", "tdd", "invisibility-guarantee"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - sdk/pyproject.toml
 - sdk/agentreplay/__init__.py
 - sdk/agentreplay/buffer.py
 - sdk/agentreplay/transport.py
 - sdk/agentreplay/wrapper.py
 - sdk/agentreplay/tool.py
 - sdk/agentreplay/state.py
 - tests/unit/test_sdk_buffer.py
 - tests/unit/test_sdk_wrapper.py
 - tests/integration/test_sdk_never_raises.py
 - scripts/demo_agent.py
 - pyproject.toml
 - specs/001-agentreplay-v1/tasks.md
 - PROGRESS.md
tests:
 - tests/unit/test_sdk_buffer.py (5 tests)
 - tests/unit/test_sdk_wrapper.py (2 tests)
 - tests/integration/test_sdk_never_raises.py (3 tests)
 - full suite 26/26 passing
---

## Prompt

start phase 4.

(Standing maintainer rules from session start: phase-by-phase, stop for
validation after each, summarize + list files every time.)

## Response snapshot

Executed Phase 4 US2 (T032–T039) with TDD. Wrote and verified-failing three
SDK test files first (caught and fixed an internal inconsistency in my own
test design — one test referenced a nonexistent agentreplay.state._state
location for the singleton before implementation existed, corrected to
match the top-level agentreplay._state design before proceeding). Then
implemented: buffer.py (contiguous 1-based seq, IngestBatch shaping, no
network), transport.py (synchronous httpx POST /ingest, every exception and
non-2xx response swallowed+logged), wrapper.py (replay.wrap() duck-types any
OpenAI-compatible client via .model_dump()/.to_dict(), recursively redacts
any "authorization" key at any nesting depth before buffering — FR-027),
tool.py (@replay.tool binds args via inspect.signature, records
result-or-error, propagates the tool's own real exceptions unaltered),
state.py (record_state_change), and __init__.py (the public API + module-
level _state singleton + AUTO_FLUSH_THRESHOLD=10 auto-flush). All 10 SDK
tests passed on first implementation attempt; full suite 26/26.

Key design decision made during implementation (not pre-specified in
research.md): chose synchronous flush() over background-thread/async
fire-and-forget for the actual network I/O, since it's deterministically
testable (T034's dead-port and erroring-server assertions need no timing
workarounds) while still satisfying "buffer in memory, batch, errors never
propagate."

Wrote scripts/demo_agent.py using a minimal hand-rolled OpenAI-compatible
client (httpx only — no `openai` package dependency) to prove wrap()'s
duck-typing genuinely works with any conforming client, not just the real
openai-python SDK. Ran the full T039 acceptance against the LIVE
containerized stack with the SAME real OpenRouter key from T031: AS-1/AS-3
verified via GET /runs/{id} (real LLM reply, real tool booking, all 4 steps
verbatim, tokens populated, zero Authorization keys); AS-2 verified by
literally stopping the backend container and re-running — exit code 0, only
a locally-logged warning, zero exceptions surfaced to the host script.
Restarted backend afterward. Cleaned test-polluted db rows three more times
during this session (recurring hazard: host pytest shares the same Postgres
as the demo evidence).

## Outcome

- ✅ Impact: The Python SDK (US2) is complete — live recording works end-to-end, and the invisibility guarantee is proven against a REAL backend outage, not a mock. Phase 4 checkpoint met.
- 🧪 Tests: 10/10 new SDK tests pass; full suite 26/26; live T039 acceptance passed against the real containerized stack with real inference (AS-1/AS-2/AS-3 all verified).
- 📁 Files: 7 SDK source files, 3 test files, 1 demo script created; pyproject.toml (pythonpath), tasks.md (T032–T039 ticked), PROGRESS.md updated. 8 per-task commits.
- 🔁 Next prompts: Phase 5 (US3 — detection at scale, T040–T042) or Phase 6 (US4 — fork safety proof via the interceptor, T043–T046); either can go next since both only depend on Phase 3's already-complete core.
- 🧠 Reflection: the recurring test-data-pollution-in-shared-db issue (flagged since Phase 3) is now a 3x-repeated manual cleanup step — worth a real fix (separate TEST_DATABASE_URL) before it causes a demo-day accident.

## Evaluation notes (flywheel)

- Failure modes observed: none in the implementation itself (10/10 tests passed on first attempt) — the only friction was my own test-file self-consistency bug (fixed before running) and the recurring db pollution (environmental, not a code defect).
- Graders run and results (PASS/FAIL): pytest full suite PASS (26/26); live demo_agent.py acceptance PASS (both AS-1/AS-3 up, and AS-2 with backend down).
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): add a TEST_DATABASE_URL (or a pytest fixture that creates/drops a throwaway schema) so pytest runs stop polluting the demo dataset — flagged three sessions running now.
