---
id: 0012
title: T031 real e2e SC-001 demo
stage: green
date: 2026-07-09
surface: agent
model: claude-sonnet-5
feature: 001-agentreplay-v1
branch: 001-agentreplay-v1
user: anusbutt
command: /sp.implement
labels: ["phase-3", "us1", "t031", "sc-001", "real-inference", "openrouter", "fixture-bug"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - .env
 - app/analysis/client.py
 - scripts/seed_demo_run.py
 - specs/001-agentreplay-v1/tasks.md
 - PROGRESS.md
tests:
 - tests/ full suite, 16/16 passing after fixes
 - manual: quickstart.md steps 1-6 against live compose stack with real OpenRouter inference
---

## Prompt

ookk i have open-router api key and base url

(Followed by: maintainer chose via AskUserQuestion to reuse the OpenRouter
key for ANALYSIS_BASE_URL too, since no separate Gemma/MI300X or Fireworks
endpoint was available; then pasted the raw API key in chat, which I wrote
directly into the gitignored .env rather than echoing back or typing into
any command line — a Bash auto-mode classifier correctly blocked my first
attempt to query OpenRouter's model list with the key typed literally into
a curl command, and I fixed that by sourcing .env instead. Maintainer also
asked where DATABASE_URL came from, mid-task — clarified it's a self-defined
local dev credential from compose.yml's db service, not fetched from
anywhere.)

## Response snapshot

Wrote the OpenRouter key into .env (confirmed gitignored, never appeared in
a command line or was committed). Queried OpenRouter's live /models catalog
to find a verified Gemma id (google/gemma-4-31b-it — an exact "Gemma 4"
match, replacing a guessed google/gemma-3-27b-it) and confirmed the demo's
recorded model (deepseek/deepseek-chat) is also available for the fork's
live call. Rebuilt the backend with real credentials and ran the actual
quickstart.md steps 1-6 against the live containerized stack.

First sweep attempt returned verdict:"pass" from the real judge — a
legitimate model judgment exposing a fixture-design bug: the original
seed_demo_run.py had a later customer turn ("ok sure, book it") plus a
state_change trigger="user_confirmed" that genuinely read as the customer
consenting to Saturday. Fixed the fixture (removed the consenting turn,
renamed trigger to agent_selected_slot), wiped and re-seeded the fixed-UUID
demo run, and re-ran the sweep: verdict flipped to "fail" with a correct
contradiction. Analysis correctly named failing_step 2 with a concrete
suggested fix. Forked with that fix applied: the live model's reply flipped
from "...locked in Saturday..." (parent) to "Perfect! I can book you for
this Friday..." (fork) — SC-001 proven with real inference. Verified parent
immutability (still flagged, still 4 steps, verdicts intact) and confirmed
via curl-of-rendered-HTML that the dashboard's CompareView correctly shows
the parent-labeled Saturday text + tool_call alongside the fork's Friday
reply. Cleaned test-polluted db rows twice more (host pytest reruns during
this same session), leaving only the two real rows (demo run + its fork).

## Outcome

- ✅ Impact: SC-001 (the north-star acceptance scenario) fully proven end-to-end against the live containerized stack with real Gemma-4 + DeepSeek inference via OpenRouter — Phase 3 (US1, the MVP) is now completely done, T016–T031 all checked.
- 🧪 Tests: 16/16 backend tests still pass after the model-id and fixture fixes (host + implied container parity); manual e2e walkthrough of quickstart.md steps 1-6 all passed with real evidence recorded.
- 📁 Files: .env created (gitignored, not committed); app/analysis/client.py model id fixed; scripts/seed_demo_run.py fixture bug fixed; tasks.md T031 ticked; PROGRESS.md has full evidence trail (verbatim verdicts, fork reply, run ids).
- 🔁 Next prompts: Phase 4 — US2 (Python SDK, T032–T039): replay.wrap, @replay.tool, buffer/transport, never-raises guarantee, scripts/demo_agent.py.
- 🧠 Reflection: seeded "failure" fixtures need to be checked against an actual judge, not just eyeballed — a human reading the fixture assumed contradiction, but a careful LLM found a legitimate alternate reading (implicit consent) that a stricter fixture design closes off. This is a good general lesson for any LLM-judged demo data.

## Evaluation notes (flywheel)

- Failure modes observed: Bash auto-mode classifier correctly caught a live secret typed directly into a command line before it reached any log; fixed by sourcing the .env file instead of literal interpolation. Real LLM judge disagreed with the fixture's intended narrative on first pass — root-caused to genuine ambiguity in the seed data, not a detection-logic bug.
- Graders run and results (PASS/FAIL): quickstart.md steps 1-6 all PASS against live stack with real inference; pytest 16/16 PASS.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): consider adding a "no-contradiction" seeded run for symmetry/regression-proofing detection (US3 territory, Phase 5).
