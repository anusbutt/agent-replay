# DATA_CONTRACT.md — the law

Every component obeys this: the SDK writes it, ingest validates it, the
timeline renders it, the fork engine reads it, the tests assert it. Do not
add, rename, or drop fields without updating this file first.

## Table: runs
- id: UUID pk
- agent_id: str, indexed
- session_id: str, indexed (e.g. FB Messenger sender id)
- status: enum(running, completed, failed, flagged)
- parent_run_id: UUID fk -> runs.id, nullable (set only on forks)
- fork_step: int, nullable (seq in parent where this fork diverged)
- run_metadata: JSONB (channel, business_id, detection verdict, analysis
  verdict, freeform)
- started_at, ended_at: timestamptz

## Table: steps
- id: UUID pk
- run_id: UUID fk -> runs.id, indexed
- seq: int (1-based per run; UNIQUE constraint on (run_id, seq))
- type: enum(llm_call, tool_call, state_change)
- input: JSONB   (shape depends on type — see below)
- output: JSONB  (shape depends on type — see below)
- latency_ms: int, nullable
- tokens_in, tokens_out: int, nullable (llm_call only)
- created_at: timestamptz

## Payload shapes — VERBATIM recording, never summarize or trim

### llm_call.input — the EXACT request sent to the model
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

### llm_call.output — the EXACT response received
```json
{
  "id": "gen-abc123",
  "choices": [{"message": {"role": "assistant",
    "content": "<full assistant reply>"}, "finish_reason": "stop"}],
  "usage": {"prompt_tokens": 512, "completion_tokens": 87}
}
```

### tool_call.input
NOTE: In Nestaro, tools are NOT LLM-native function calls (the request sends
no tools array). A tool_call is a real Python function with side effects
(e.g. book_appointment) invoked after the text response is parsed, captured
via the `@replay.tool` decorator. These are what the fork engine intercepts.
```json
{"name": "book_appointment",
 "args": {"day": "saturday", "time": "14:00", "customer_id": "cust_991"}}
```

### tool_call.output
```json
{"result": {"booking_id": "bk_204", "confirmed": true}, "error": null}
```

### state_change.input / .output
```json
{"from_state": "QUOTING", "to_state": "BOOKING", "trigger": "user_confirmed"}
```