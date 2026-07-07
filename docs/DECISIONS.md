# DECISIONS.md — pinned decisions + scope guard

These are settled. Do not re-decide them inside a session. If a task appears
to require contradicting one, STOP and ask — this file is the tiebreaker.

## Pinned decisions

1. **Fork = new run.** A fork is a new row in `runs` with `parent_run_id` and
   `fork_step` set. The parent run and its steps are NEVER modified.

2. **Conversation-level replay, not program-level.** Reconstruct the recorded
   `llm_call.input` at the fork step, apply the user's modification, call the
   model live from there. We do NOT re-execute the agent's application code.

3. **Tool interception during forks.** Match a cached result by (run_id, seq)
   positionally; fallback match by sha256(name + canonical_json(args)); no
   match -> return typed mock `{"result": {"mocked": true}, "error": null}`.
   A forked run NEVER executes a real tool. No exceptions, no side effects.

4. **Forked LLM calls run at temperature 0** unless the fork request
   explicitly overrides. Replay tests fidelity of context, not model chance.

5. **The SDK must never raise into host agent code.** All transport/recording
   errors are swallowed and logged locally. A recording failure must be
   invisible to the agent it records.

6. **Verdicts live on run metadata.** Detection and analysis results are
   stored as JSONB under `run_metadata.detection` and `run_metadata.analysis`.

7. **Docker containerization is a must-do delivery step.** Full-stack
   containerization via compose: one image/container per service — backend
   (FastAPI), frontend (dashboard), and db (Postgres) — NEVER a single
   combined "monster" image. `docker compose up` wires up all three from the
   repo's compose file. The backend image (built from a Dockerfile in the
   repo) is also the deploy artifact; the frontend Dockerfile serves
   local/demo use (Vercel remains the hosted target). Containers are
   configured via environment variables only; no secrets baked into images;
   no container-specific code paths. The SDK is an embedded library and is
   not containerized.

## Scope guard — NOT in V1

Do not build, scaffold, or "prepare for" any of these. If a task seems to
need one, STOP and say so instead of building it.

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