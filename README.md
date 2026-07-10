# AgentReplay

A flight recorder and time-travel debugger for AI agents.

A Python SDK records every step of an agent's execution (LLM calls, tool
calls, state changes) invisibly. When a run goes wrong, a developer opens
the timeline, gets an AI root-cause analysis, and — the core feature —
**forks** the run from the failing step with a fix applied. The fork uses
live inference but sandboxed tool calls, so the developer can verify the fix
against the exact conversation that failed, with zero real-world side
effects.

Built solo for the **AMD Developer Hackathon ACT II** (Jul 6–11, 2026).
Demo agent: **Nestaro**, a lead-qualification agent for home service
businesses. The north-star scenario: a customer asks for a Friday
appointment, Nestaro books Saturday instead — AgentReplay detects the
contradiction, explains why it happened, and proves a one-line prompt fix
resolves it, without ever touching the real booking system.

## AMD Compute Usage

Analysis inference for the public hosted demo runs **Gemma 4 via
OpenRouter** (provider-swappable through `ANALYSIS_BASE_URL` /
`ANALYSIS_API_KEY` / `ANALYSIS_MODEL`).

**AMD compute is demonstrated separately in [`amd/`](amd/):**
AgentReplay's real root-cause analysis prompt — imported unmodified from
[`app/analysis/prompts.py`](app/analysis/prompts.py) — was executed
against a real recorded run on an **AMD Radeon gfx1100** (RDNA3, 48GB,
ROCm 7.2) using **PyTorch built for ROCm** (`torch.version.hip`
populated, `torch.version.cuda` `None`). The model loaded on the AMD GPU
is **Qwen2.5-1.5B-Instruct** (see `MODEL_ID` in
[`amd/run_analysis_on_amd.py`](amd/run_analysis_on_amd.py)); a smaller
model was chosen because the hackathon pod's 24-hour window and download
bandwidth made the 26B Gemma weights (~50GB) infeasible — the requirement
is AMD compute usage, not model scale.

The committed evidence in [`amd/`](amd/) includes the exact script, the
exact prompt sent, the verdict the model produced, the ROCm/PyTorch
environment fingerprint, and `rocm-smi` output captured while the model
occupied VRAM on the gfx1100 device.

## Architecture

Agent code wraps its LLM client with `replay.wrap(client)` and decorates
tools with `@replay.tool`. Recorded events buffer in memory and flush in
batches to `POST /ingest` on the FastAPI backend, which persists them to
Postgres (fixed columns for structure, JSONB for payloads). The Next.js
dashboard reads runs and renders timelines, verdicts, and a side-by-side
fork comparison. The replay engine — same FastAPI process — reconstructs a
run's recorded context to execute a single-shot fork: exactly one live LLM
call at the chosen step, at temperature 0, with the fix applied. A tool
interceptor guarantees a forked run never executes a real tool, matching a
cached result positionally or by content hash before falling back to a
typed mock. An analysis layer sends serialized runs to an LLM judge (Gemma
4 via OpenRouter, an OpenAI-compatible endpoint, provider-swappable via
env vars) for detection and root-cause verdicts, stored as JSONB on the
run's own metadata. The same analysis pipeline has been executed on AMD
hardware — see [AMD Compute Usage](#amd-compute-usage).

## Getting started

See **[the quickstart](specs/001-agentreplay-v1/quickstart.md)** for the
full walkthrough: bring up the stack, seed the demo run, detect, analyze,
fork, and compare — from a clean checkout to the demo moment.

Short version:

```bash
cp .env.example .env   # fill in the real values below
docker compose up
python scripts/seed_demo_run.py
```

Then open `http://localhost:3000`.

## Environment variables

All configuration is via environment variables — no secrets in code, no
container-specific code paths (constitution Principle VII).

| Variable | Purpose | Default (local compose) |
|---|---|---|
| `DATABASE_URL` | Postgres connection string | set by `compose.yml` for the local stack; NeonDB URL for hosted |
| `AGENTREPLAY_API_KEY` | The single static API key protecting every backend endpoint | none — must be set |
| `ANALYSIS_BASE_URL` | OpenAI-compatible endpoint for detection/analysis (Gemma 4 via OpenRouter; swap providers by changing this URL, the key, and `ANALYSIS_MODEL`) | `https://openrouter.ai/api/v1` |
| `ANALYSIS_API_KEY` | Key for the analysis endpoint | none — must be set |
| `ANALYSIS_MODEL` | Model id for the analysis endpoint (format is provider-specific) | `google/gemma-4-31b-it` |
| `REPLAY_BASE_URL` | OpenAI-compatible endpoint for forked LLM calls | `https://openrouter.ai/api/v1` |
| `REPLAY_API_KEY` | Key for the replay/fork endpoint | none — must be set |

The dashboard additionally reads two build-time variables (see
`compose.yml`'s `frontend.build.args` and `dashboard/Dockerfile`):
`NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000`) and
`NEXT_PUBLIC_AGENTREPLAY_API_KEY` (mirrors `AGENTREPLAY_API_KEY` — the
dashboard's own client-side action buttons need the same key to call the
API). A server-only `API_BASE_URL_INTERNAL` (default `http://backend:8000`)
lets the dashboard's server-rendered pages reach the backend over the
Docker network, distinct from the browser-facing URL.

## Stack

Python 3.11+ SDK (httpx only) · FastAPI + SQLModel backend · Postgres
(NeonDB hosted, local container via compose) · Next.js + TypeScript +
Tailwind dashboard · Gemma 4 via OpenRouter for analysis, an
OpenAI-compatible endpoint. No LangChain, no LangGraph, no ORM beyond
SQLModel, no message queues — see `.specify/memory/constitution.md` for the
full set of pinned decisions this project doesn't re-litigate.

## Running the stack

Three containers, one per service, wired by `docker compose up` — backend
(`:8000`), frontend (`:3000`), db (`:5432`). See `Dockerfile` and
`dashboard/Dockerfile`. Run the test suite inside the backend container with
`docker compose exec backend pytest`.

## What's not here

See [`ROADMAP.md`](ROADMAP.md) for what's deliberately out of scope for V1
(and why) — extra auth, multi-tenancy, rate limiting, OTel, framework
integrations, streaming ingestion, one-click fix deploys.
