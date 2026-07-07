# Phase 1 Data Model: AgentReplay V1

**Source of law**: docs/DATA_CONTRACT.md — this file maps that contract onto
SQLModel entities 1:1. Field names, enum values, and payload shapes are
transcribed, not designed. Do not add, rename, or drop fields without
updating docs/DATA_CONTRACT.md first (constitution: Data Contract Supremacy).

## Entity: Run (table `runs`)

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | primary key |
| agent_id | str | indexed |
| session_id | str | indexed (e.g. FB Messenger sender id) |
| status | enum(running, completed, failed, flagged) | required |
| parent_run_id | UUID | fk -> runs.id, nullable (set only on forks) |
| fork_step | int | nullable (seq in parent where this fork diverged) |
| run_metadata | JSONB | channel, business_id, detection verdict, analysis verdict, freeform |
| started_at | timestamptz | |
| ended_at | timestamptz | nullable until run ends |

**Relationships**: self-referential — a fork points at its parent via
`parent_run_id`; a run has many `steps` (1:N on `steps.run_id`). A fork
copies `agent_id` and `session_id` from its parent and stores only its own
new step(s) — in V1's single-shot model, exactly one live llm_call step at
`seq` 1 (the shared prefix remains in the parent; CompareView renders parent
steps as parent-labeled context — research R4).

**Validation rules** (from spec FRs):
- `status` must be one of the four enum values (FR-008).
- `parent_run_id` and `fork_step` are set together, only on forks (FR-014).
- Detection verdict lives ONLY at `run_metadata.detection`; analysis verdict
  ONLY at `run_metadata.analysis` (FR-020, FR-022). Verdict writes merge into
  existing `run_metadata` — they never replace the whole object.

**State transitions** (`status`):
```
running → completed   (agent finished normally, via SDK end_run)
running → failed      (agent errored / fork engine error)
running|completed → flagged   (detection sweep found a contradiction)
```
Ingest never downgrades `flagged` (research R2 upsert protections).
Parent-run immutability (constitution I) applies to recorded steps and fork
lineage fields, not to `status`/`run_metadata`/`ended_at`, which the
ingest/detection/analysis paths legitimately update on the run itself.
A fork NEVER updates any field of its parent.

## Entity: Step (table `steps`)

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | primary key |
| run_id | UUID | fk -> runs.id, indexed |
| seq | int | 1-based per run; UNIQUE constraint on (run_id, seq) |
| type | enum(llm_call, tool_call, state_change) | required |
| input | JSONB | shape depends on type — see payload shapes |
| output | JSONB | shape depends on type — see payload shapes |
| latency_ms | int | nullable |
| tokens_in | int | nullable (llm_call only) |
| tokens_out | int | nullable (llm_call only) |
| created_at | timestamptz | |

**Validation rules** (from spec FRs):
- `seq` is the recorder's truth: 1-based, contiguous per run (FR-003);
  duplicates rejected by UNIQUE (run_id, seq) (FR-008).
- `input`/`output` are VERBATIM — never summarized, never trimmed (FR-002).
- `tokens_in`/`tokens_out` populated only for `type = llm_call` (FR-006).

## Payload shapes — VERBATIM recording, never summarize or trim (from docs/DATA_CONTRACT.md)

llm_call.input — the EXACT request sent to the model

Nestaro sends a bare single-shot text completion: no tools, no tool_choice,
no response_format, no streaming. Record exactly these fields:

```json
{
  "model": "deepseek/deepseek-chat",
  "messages": [
    {"role": "system", "content": "<full system prompt as sent>"},
    {"role": "user", "content": "Previous conversation:\n<history>"},
    {"role": "user", "content": "I need duct cleaning Friday"}
  ],
  "max_tokens": 1024,
  "temperature": 0.7,
  "headers": {"HTTP-Referer": "https://nestaro.com",
              "X-Title": "Nestaro Lead Qualifier"}
}
```

RULES:
- The messages array is recorded EXACTLY as sent, in order. The optional
  second `user` message ("Previous conversation:\n...") is part of the
  context the model saw and MUST be captured verbatim in position — the fork
  engine reconstructs from this, so any drift here corrupts replay.
- Record HTTP-Referer and X-Title for fidelity. NEVER record the
  Authorization header or any bearer token — redact at the SDK boundary.
- The fork engine supplies its own credentials; it needs the messages and
  params to replay, not the original auth.

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

NOTE: In Nestaro, tools are NOT LLM-native function calls (the request sends
no tools array). A tool_call is a real Python function with side effects
(e.g. book_appointment) invoked after the text response is parsed, captured
via the `@replay.tool` decorator. These are what the fork engine intercepts.

```json
{"name": "book_appointment",
 "args": {"day": "saturday", "time": "14:00", "customer_id": "cust_991"}}
```

tool_call.output:

```json
{"result": {"booking_id": "bk_204", "confirmed": true}, "error": null}
```

state_change.input / .output:

```json
{"from_state": "QUOTING", "to_state": "BOOKING", "trigger": "user_confirmed"}
```

## Verdict shapes (stored inside `run_metadata`, per R5)

`run_metadata.detection`:

```json
{"verdict": "fail", "reason": "Customer asked for Friday; agent booked Saturday.",
 "contradiction": {"user_intent": "appointment on Friday",
                   "agent_action": "booked saturday 14:00"}}
```

`run_metadata.analysis`:

```json
{"failing_step": 6, "root_cause": "System prompt never instructs the agent to confirm the requested day before booking.",
 "suggested_fix": "Add to system prompt: 'Always book the exact day the customer requested; if unavailable, ask before proposing another day.'"}
```

(Verdict shapes are implementation-level, defined in research.md R5; they
live inside the JSONB `run_metadata` field and therefore do not alter the
data contract's column set.)

## SQLModel mapping notes

- Both entities live in `app/models.py` (convention).
- Enums: Python `str`-enums persisted as text with a CHECK-equivalent via
  SQLModel/SQLAlchemy Enum; values byte-identical to the contract.
- JSONB columns via SQLAlchemy `JSONB` (Postgres dialect).
- Schema bootstrap: `SQLModel.metadata.create_all` on startup (research R7).
