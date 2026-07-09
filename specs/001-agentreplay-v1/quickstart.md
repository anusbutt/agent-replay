# Quickstart: AgentReplay V1

From clean checkout to the Friday/Saturday demo (spec SC-001, SC-008).

## Prerequisites

- Docker with the compose plugin (`docker compose version`)
- Copies of the required env vars (see `.env.example`):

```bash
cp .env.example .env
# fill in:
# DATABASE_URL          — set automatically for compose; NeonDB URL for hosted
# AGENTREPLAY_API_KEY   — the single static API key
# ANALYSIS_BASE_URL     — Gemma 4 endpoint via OpenRouter (Fireworks/AMD-hosted target once deployed)
# ANALYSIS_API_KEY      — key for the analysis endpoint
# REPLAY_BASE_URL       — OpenAI-compatible endpoint for forked LLM calls (default OpenRouter)
# REPLAY_API_KEY        — key for the replay endpoint
```

## 1. Bring up the stack (one command — constitution VII)

```bash
docker compose up
```

Three services, one container each (never a single combined image):

| Service | What | Port |
|---------|------|------|
| backend | FastAPI ingest + replay/fork + analysis/detection | 8000 |
| frontend | Next.js dashboard | 3000 |
| db | Postgres 16 (named volume) | 5432 |

Backend creates the schema on startup. Verify:

```bash
curl -s http://localhost:8000/runs -H "Authorization: Bearer $AGENTREPLAY_API_KEY"
# → []
```

## 2. Record (or seed) the Nestaro Friday/Saturday run

Live recording — inside the agent:

```python
import agentreplay as replay

replay.init(base_url="http://localhost:8000", api_key="...", agent_id="nestaro")
client = replay.wrap(openai_client)      # records every llm_call verbatim

@replay.tool
def book_appointment(day: str, time: str, customer_id: str): ...

# ... conversation runs ...
replay.end_run()   # finalizes: status=completed, ended_at set, buffer flushed
```

Or seed the demo fixture (a recorded run where the customer asks for Friday
and the agent books Saturday) straight into the ingest API:

```bash
python scripts/seed_demo_run.py   # POSTs a data-contract-conformant batch to /ingest
```

## 3. Detect — flag the contradiction

```bash
curl -s -X POST http://localhost:8000/detect/sweep \
  -H "Authorization: Bearer $AGENTREPLAY_API_KEY"
```

Expected: the seeded run comes back `verdict: fail` (user asked Friday, agent
booked Saturday), its status flips to `flagged`, verdict stored at
`run_metadata.detection`.

## 4. Analyze — root cause + suggested fix

```bash
curl -s -X POST http://localhost:8000/runs/<RUN_ID>/analyze \
  -H "Authorization: Bearer $AGENTREPLAY_API_KEY"
```

Expected: `{"failing_step": <seq>, "root_cause": "...", "suggested_fix": "..."}`
stored at `run_metadata.analysis`.

## 5. Fork — verify the fix with zero real side effects

```bash
curl -s -X POST http://localhost:8000/runs/<RUN_ID>/fork \
  -H "Authorization: Bearer $AGENTREPLAY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fork_step": <failing_step>,
       "modification": {"system_prompt": "<recorded prompt + suggested fix>"}}'
```

The engine reconstructs the recorded context at the fork step, applies the
fix, and executes exactly ONE live model call at temperature 0 (single-shot,
research R4). Nestaro's tools are not LLM-native, so no tool call is issued
and no real booking can happen — the interceptor (positional → hash → typed
mock) stands guard for any tool-emitting replay.

## 6. Compare — the demo moment

Open http://localhost:3000, click the flagged run, open its fork: the
side-by-side view shows the original's assistant text and its parent-labeled
`book_appointment` tool_call booking **saturday** against the fork's
assistant reply choosing **friday** — the model's decision flipped.

## Running checks

```bash
docker compose exec backend pytest          # backend + contract tests
```

## Hosted deploy (reference)

- backend: Railway deploys the root `Dockerfile`; `DATABASE_URL` → NeonDB.
- frontend: Vercel builds `dashboard/` (container remains for local/demo).
- Switching analysis to the Fireworks fallback = change `ANALYSIS_BASE_URL`
  (and key); nothing else.
