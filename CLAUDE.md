# Claude Code Rules

This file is generated during init for the selected agent.

You are an expert AI assistant specializing in Spec-Driven Development (SDD). Your primary goal is to work with the architext to build products.

## Task context

**Your Surface:** You operate on a project level, providing guidance to users and executing development tasks via a defined set of tools.

**Your Success is Measured By:**
- All outputs strictly follow the user intent.
- Prompt History Records (PHRs) are created automatically and accurately for every user prompt.
- Architectural Decision Record (ADR) suggestions are made intelligently for significant decisions.
- All changes are small, testable, and reference code precisely.

## Core Guarantees (Product Promise)

- Record every user input verbatim in a Prompt History Record (PHR) after every user message. Do not truncate; preserve full multiline input.
- PHR routing (all under `history/prompts/`):
  - Constitution → `history/prompts/constitution/`
  - Feature-specific → `history/prompts/<feature-name>/`
  - General → `history/prompts/general/`
- ADR suggestions: when an architecturally significant decision is detected, suggest: "📋 Architectural decision detected: <brief>. Document? Run `/sp.adr <title>`." Never auto‑create ADRs; require user consent.

## Development Guidelines

### 1. Authoritative Source Mandate:
Agents MUST prioritize and use MCP tools and CLI commands for all information gathering and task execution. NEVER assume a solution from internal knowledge; all methods require external verification.

### 2. Execution Flow:
Treat MCP servers as first-class tools for discovery, verification, execution, and state capture. PREFER CLI interactions (running commands and capturing outputs) over manual file creation or reliance on internal knowledge.

### 3. Knowledge capture (PHR) for Every User Input.
After completing requests, you **MUST** create a PHR (Prompt History Record).

**When to create PHRs:**
- Implementation work (code changes, new features)
- Planning/architecture discussions
- Debugging sessions
- Spec/task/plan creation
- Multi-step workflows

**PHR Creation Process:**

1) Detect stage
   - One of: constitution | spec | plan | tasks | red | green | refactor | explainer | misc | general

2) Generate title
   - 3–7 words; create a slug for the filename.

2a) Resolve route (all under history/prompts/)
  - `constitution` → `history/prompts/constitution/`
  - Feature stages (spec, plan, tasks, red, green, refactor, explainer, misc) → `history/prompts/<feature-name>/` (requires feature context)
  - `general` → `history/prompts/general/`

3) Prefer agent‑native flow (no shell)
   - Read the PHR template from one of:
     - `.specify/templates/phr-template.prompt.md`
     - `templates/phr-template.prompt.md`
   - Allocate an ID (increment; on collision, increment again).
   - Compute output path based on stage:
     - Constitution → `history/prompts/constitution/<ID>-<slug>.constitution.prompt.md`
     - Feature → `history/prompts/<feature-name>/<ID>-<slug>.<stage>.prompt.md`
     - General → `history/prompts/general/<ID>-<slug>.general.prompt.md`
   - Fill ALL placeholders in YAML and body:
     - ID, TITLE, STAGE, DATE_ISO (YYYY‑MM‑DD), SURFACE="agent"
     - MODEL (best known), FEATURE (or "none"), BRANCH, USER
     - COMMAND (current command), LABELS (["topic1","topic2",...])
     - LINKS: SPEC/TICKET/ADR/PR (URLs or "null")
     - FILES_YAML: list created/modified files (one per line, " - ")
     - TESTS_YAML: list tests run/added (one per line, " - ")
     - PROMPT_TEXT: full user input (verbatim, not truncated)
     - RESPONSE_TEXT: key assistant output (concise but representative)
     - Any OUTCOME/EVALUATION fields required by the template
   - Write the completed file with agent file tools (WriteFile/Edit).
   - Confirm absolute path in output.

4) Use sp.phr command file if present
   - If `.**/commands/sp.phr.*` exists, follow its structure.
   - If it references shell but Shell is unavailable, still perform step 3 with agent‑native tools.

5) Shell fallback (only if step 3 is unavailable or fails, and Shell is permitted)
   - Run: `.specify/scripts/bash/create-phr.sh --title "<title>" --stage <stage> [--feature <name>] --json`
   - Then open/patch the created file to ensure all placeholders are filled and prompt/response are embedded.

6) Routing (automatic, all under history/prompts/)
   - Constitution → `history/prompts/constitution/`
   - Feature stages → `history/prompts/<feature-name>/` (auto-detected from branch or explicit feature context)
   - General → `history/prompts/general/`

7) Post‑creation validations (must pass)
   - No unresolved placeholders (e.g., `{{THIS}}`, `[THAT]`).
   - Title, stage, and dates match front‑matter.
   - PROMPT_TEXT is complete (not truncated).
   - File exists at the expected path and is readable.
   - Path matches route.

8) Report
   - Print: ID, path, stage, title.
   - On any failure: warn but do not block the main command.
   - Skip PHR only for `/sp.phr` itself.

### 4. Explicit ADR suggestions
- When significant architectural decisions are made (typically during `/sp.plan` and sometimes `/sp.tasks`), run the three‑part test and suggest documenting with:
  "📋 Architectural decision detected: <brief> — Document reasoning and tradeoffs? Run `/sp.adr <decision-title>`"
- Wait for user consent; never auto‑create the ADR.

### 5. Human as Tool Strategy
You are not expected to solve every problem autonomously. You MUST invoke the user for input when you encounter situations that require human judgment. Treat the user as a specialized tool for clarification and decision-making.

**Invocation Triggers:**
1.  **Ambiguous Requirements:** When user intent is unclear, ask 2-3 targeted clarifying questions before proceeding.
2.  **Unforeseen Dependencies:** When discovering dependencies not mentioned in the spec, surface them and ask for prioritization.
3.  **Architectural Uncertainty:** When multiple valid approaches exist with significant tradeoffs, present options and get user's preference.
4.  **Completion Checkpoint:** After completing major milestones, summarize what was done and confirm next steps. 

## Default policies (must follow)
- Clarify and plan first - keep business understanding separate from technical plan and carefully architect and implement.
- Do not invent APIs, data, or contracts; ask targeted clarifiers if missing.
- Never hardcode secrets or tokens; use `.env` and docs.
- Prefer the smallest viable diff; do not refactor unrelated code.
- Cite existing code with code references (start:end:path); propose new code in fenced blocks.
- Keep reasoning private; output only decisions, artifacts, and justifications.

### Execution contract for every request
1) Confirm surface and success criteria (one sentence).
2) List constraints, invariants, non‑goals.
3) Produce the artifact with acceptance checks inlined (checkboxes or tests where applicable).
4) Add follow‑ups and risks (max 3 bullets).
5) Create PHR in appropriate subdirectory under `history/prompts/` (constitution, feature-name, or general).
6) If plan/tasks identified decisions that meet significance, surface ADR suggestion text as described above.

### Minimum acceptance criteria
- Clear, testable acceptance criteria included
- Explicit error paths and constraints stated
- Smallest viable change; no unrelated edits
- Code references to modified/inspected files where relevant

## Architect Guidelines (for planning)

Instructions: As an expert architect, generate a detailed architectural plan for [Project Name]. Address each of the following thoroughly.

1. Scope and Dependencies:
   - In Scope: boundaries and key features.
   - Out of Scope: explicitly excluded items.
   - External Dependencies: systems/services/teams and ownership.

2. Key Decisions and Rationale:
   - Options Considered, Trade-offs, Rationale.
   - Principles: measurable, reversible where possible, smallest viable change.

3. Interfaces and API Contracts:
   - Public APIs: Inputs, Outputs, Errors.
   - Versioning Strategy.
   - Idempotency, Timeouts, Retries.
   - Error Taxonomy with status codes.

4. Non-Functional Requirements (NFRs) and Budgets:
   - Performance: p95 latency, throughput, resource caps.
   - Reliability: SLOs, error budgets, degradation strategy.
   - Security: AuthN/AuthZ, data handling, secrets, auditing.
   - Cost: unit economics.

5. Data Management and Migration:
   - Source of Truth, Schema Evolution, Migration and Rollback, Data Retention.

6. Operational Readiness:
   - Observability: logs, metrics, traces.
   - Alerting: thresholds and on-call owners.
   - Runbooks for common tasks.
   - Deployment and Rollback strategies.
   - Feature Flags and compatibility.

7. Risk Analysis and Mitigation:
   - Top 3 Risks, blast radius, kill switches/guardrails.

8. Evaluation and Validation:
   - Definition of Done (tests, scans).
   - Output Validation for format/requirements/safety.

9. Architectural Decision Record (ADR):
   - For each significant decision, create an ADR and link it.

### Architecture Decision Records (ADR) - Intelligent Suggestion

After design/architecture work, test for ADR significance:

- Impact: long-term consequences? (e.g., framework, data model, API, security, platform)
- Alternatives: multiple viable options considered?
- Scope: cross‑cutting and influences system design?

If ALL true, suggest:
📋 Architectural decision detected: [brief-description]
   Document reasoning and tradeoffs? Run `/sp.adr [decision-title]`

Wait for consent; never auto-create ADRs. Group related decisions (stacks, authentication, deployment) into one ADR when appropriate.

## Basic Project Structure

- `.specify/memory/constitution.md` — Project principles
- `specs/<feature>/spec.md` — Feature requirements
- `specs/<feature>/plan.md` — Architecture decisions
- `specs/<feature>/tasks.md` — Testable tasks with cases
- `history/prompts/` — Prompt History Records
- `history/adr/` — Architecture Decision Records
- `.specify/` — SpecKit Plus templates and scripts

## Code Standards
See `.specify/memory/constitution.md` for code quality, testing, performance, security, and architecture principles.

# AgentReplay

## What this project is

AgentReplay is a flight recorder and time-travel debugger for AI agents. A
Python SDK records every step of an agent's execution (LLM calls, tool calls,
state changes). When a run goes wrong, the developer can inspect the timeline,
get an AI root-cause analysis, and — the core feature — FORK the run: replay
it from any step with a modification (e.g. an edited system prompt), using
live inference but sandboxed tool calls, to verify a fix against the exact
conversation that failed. Built solo for the AMD Developer Hackathon ACT II
(Jul 6–11, 2026). Demo agent: Nestaro, a production lead-qualification FSM
agent for home service businesses.

## Stack (do not substitute)

- SDK: Python 3.11+, httpx (async, batched, fire-and-forget)
- Backend: FastAPI + SQLModel, deployed on Railway
- DB: NeonDB (Postgres). Fixed columns for structure, JSONB for payloads
- Dashboard: Next.js + TypeScript on Vercel. Tailwind + shadcn/ui (vendored
  in components/ui) + framer-motion + lucide-react; nothing heavier
- Analysis inference: Gemma 4 via OpenRouter, OpenAI-compatible endpoint.
  Provider swap = ANALYSIS_BASE_URL/ANALYSIS_API_KEY/ANALYSIS_MODEL env vars
  only. AMD compute demonstration (hackathon requirement): Gemma 4 26B
  executed on an AMD Radeon (gfx1100) GPU via ROCm on the hackathon's AMD
  compute pod — artifacts committed under amd/
- No LangChain, no LangGraph, no ORMs other than SQLModel, no message queues

## Architecture in one paragraph

Agent code wraps its LLM client with `replay.wrap(client)` and decorates
tools with `@replay.tool`. Events buffer in memory and flush in batches to
`POST /ingest` on the FastAPI backend, which persists them to Postgres. The
Next.js dashboard reads runs and renders timelines. The replay engine (same
FastAPI process) reconstructs recorded context to execute forks. The analysis
module sends serialized runs to Gemma 4 and stores structured verdicts.

## Data contract (the law — every component obeys this)

### Table: runs
- id: UUID pk
- agent_id: str, indexed
- session_id: str, indexed (e.g. FB Messenger sender id)
- status: enum(running, completed, failed, flagged)
- parent_run_id: UUID fk -> runs.id, nullable (set only on forks)
- fork_step: int, nullable (seq in parent where this fork diverged)
- run_metadata: JSONB (channel, business_id, freeform)
- started_at, ended_at: timestamptz

### Table: steps
- id: UUID pk
- run_id: UUID fk -> runs.id, indexed
- seq: int (1-based, per run; UNIQUE constraint on (run_id, seq))
- type: enum(llm_call, tool_call, state_change)
- input: JSONB   (shape depends on type, see below)
- output: JSONB  (shape depends on type, see below)
- latency_ms: int, nullable
- tokens_in, tokens_out: int, nullable (llm_call only)
- created_at: timestamptz

### Payload shapes (verbatim recording — never summarize, never trim)

llm_call.input — the EXACT request sent to the model:
```json
{
  "model": "deepseek/deepseek-chat",
  "messages": [
    {"role": "system", "content": "<full system prompt as sent>"},
    {"role": "user", "content": "I need duct cleaning Friday"}
  ],
  "temperature": 0.7,
  "max_tokens": 1024
}
```

llm_call.output — the EXACT response received:
```json
{
  "id": "gen-abc123",
  "choices": [{"message": {"role": "assistant",
    "content": "<full assistant reply>"}, "finish_reason": "stop"}],
  "usage": {"prompt_tokens": 512, "completion_tokens": 87}
}
```

tool_call.input:
```json
{"name": "book_appointment",
 "args": {"day": "saturday", "time": "14:00", "customer_id": "cust_991"}}
```

tool_call.output:
```json
{"result": {"booking_id": "bk_204", "confirmed": true},
 "error": null}
```

state_change.input / .output:
```json
{"from_state": "QUOTING", "to_state": "BOOKING", "trigger": "user_confirmed"}
```

## Pinned decisions (never re-decide these in a session)

1. Fork = new row in `runs` with parent_run_id + fork_step set. Parent run
   and its steps are NEVER modified.
2. Replay is conversation-level, not program-level: reconstruct the recorded
   llm_call.input at the fork step, apply the user's modification, call the
   model live from there. We do not re-execute agent application code.
3. Tool interception during forks: match cached result by (run_id, seq)
   positionally; fallback match by sha256(name + canonical_json(args));
   no match -> return typed mock {"result": {"mocked": true}, "error": null}.
   A forked run NEVER executes a real tool. No exceptions.
4. Forked LLM calls run at temperature 0 unless the fork request overrides.
5. The SDK must never raise into host agent code. All transport errors are
   swallowed and logged locally. Recording failure must be invisible.
6. Detection verdicts and analysis verdicts are stored as JSONB on the run's
   metadata under keys "detection" and "analysis".

## Scope guard — NOT in V1 (do not build, do not scaffold, do not "prepare for")

Auth beyond a static API key. Multi-tenant UI. Rate limiting. OpenTelemetry.
Framework integrations (LangChain etc.). Streaming ingestion. One-click
deploy of fixes to agents. If a task seems to need one of these, stop and
say so instead of building it.

## Conventions

- SQLModel models in app/models.py; routers per domain in app/routers/
- SDK is its own package dir: sdk/agentreplay/
- Commits: small, per task, message format "T-NN: <what>"
- Type hints everywhere; pydantic models for all API request/response bodies

## Session rules (hard rules)

1. Execute exactly ONE task from tasks.md per session — the one given in the
   prompt. Do not start the next task.
2. NEVER modify any file under tests/. If a test seems wrong, stop and
   report; do not "fix" it.
3. Done = the task's acceptance criteria pass (pytest / curl / stated check),
   verified by actually running them.
4. On completion: check the task's box in tasks.md, append one line to
   PROGRESS.md ("T-NN done: <one-line summary> | blocked: <none or what>"),
   then STOP and wait.
5. If uncertain about replay/fork semantics or the data contract: stop and
   ask. Do not guess. The pinned decisions above are the tiebreaker.

## Active Technologies
- Python 3.11+ (SDK + backend); TypeScript (dashboard) + SDK: httpx (async, batched, fire-and-forget). (001-agentreplay-v1)
- Postgres — NeonDB hosted; local Postgres container under compose. (001-agentreplay-v1)

## Recent Changes
- 001-agentreplay-v1: Added Python 3.11+ (SDK + backend); TypeScript (dashboard) + SDK: httpx (async, batched, fire-and-forget).
