# ROADMAP.md

Items deliberately excluded from AgentReplay V1's scope (per
`docs/DECISIONS.md`'s scope guard and the project constitution). None of
these are built, scaffolded, or "prepared for" in the current codebase — if
a future task seems to need one, it belongs here first, then gets promoted
out of this file when actually undertaken.

## Auth beyond a single static API key

V1 protects every endpoint with one static `Authorization: Bearer
$AGENTREPLAY_API_KEY`. A production/multi-user deployment would need real
user accounts, session management, and per-user API keys — likely OAuth2 or
a managed auth provider (Clerk, Auth0) rather than hand-rolled sessions.

## Multi-tenant UI

The dashboard currently has no concept of an organization or workspace — all
runs across all agents are visible to anyone with the API key. Multi-tenancy
would require a `tenant_id` on every table, tenant-scoped queries
everywhere, and a UI for switching between tenants.

## Rate limiting

No request throttling exists on any endpoint. A public deployment would need
per-key rate limits (e.g. via a Redis-backed token bucket or a gateway like
Kong/Envoy) to prevent abuse of the ingest and analysis endpoints, both of
which have real cost (Postgres writes, LLM inference calls).

## OpenTelemetry / OTel compatibility

AgentReplay *is* an observability tool for AI agents, but it doesn't emit or
consume standard OTel traces/spans/metrics itself. A future integration
could export recorded runs as OTel traces (each step as a span) for
interop with existing observability stacks (Grafana, Datadog, Honeycomb).

## Framework integrations (LangChain, LangGraph, etc.)

The SDK is deliberately framework-agnostic — `replay.wrap()` duck-types any
OpenAI-compatible client, and `@replay.tool` works on any Python function.
Dedicated adapters for LangChain callbacks, LangGraph node instrumentation,
or CrewAI hooks would reduce integration friction for agents already built
on those frameworks, at the cost of a maintenance surface per framework.

## Streaming ingestion

The ingest API is request/response batch-only — the SDK buffers events and
POSTs a batch. A future version could support a persistent connection
(WebSocket or gRPC stream) for lower-latency live-tailing of an in-progress
run in the dashboard, rather than the current poll/refresh model.

## One-click deploy of a fix to a live agent

The fork panel lets a developer verify a system-prompt fix against the exact
failing conversation, but shipping that fix to the live agent is a manual
copy-paste today. This is a deliberate human gate on an irreversible
action, not a missing feature — a future "promote fix" button would need a
real deployment target (the host agent's actual prompt-config store) and a
clear rollback story before it's safe to automate.

---

## Also noted, not yet promoted

- **Separate test database for CI**: V1 now isolates local pytest runs onto
  a dedicated `<dbname>_test` database (see `tests/conftest.py`), but this
  isn't yet wired into a CI pipeline — there is no CI in V1.
- **Alembic migrations**: schema bootstrap is `SQLModel.metadata.create_all`
  (idempotent, no migration history). Fine for two tables at hackathon
  scale; would need real migrations before any production schema change.
