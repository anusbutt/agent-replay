"""Seed the Nestaro Friday/Saturday demo run into the ingest API.

POSTs a completed, data-contract-conformant run in which the customer asks for
FRIDAY and the agent books SATURDAY — the primary acceptance scenario's input
(spec US1). Payload shapes are byte-identical to docs/DATA_CONTRACT.md:
- messages recorded EXACTLY as sent, including the "Previous conversation:"
  history user message in position;
- HTTP-Referer / X-Title headers recorded; NO Authorization key anywhere;
- tool_call is Nestaro's real Python function (not LLM-native).

Usage: python scripts/seed_demo_run.py
Env: AGENTREPLAY_BASE_URL (default http://localhost:8000),
     AGENTREPLAY_API_KEY  (default dev-key — the compose default).
"""

import os
import sys

import httpx

BASE_URL = os.environ.get("AGENTREPLAY_BASE_URL", "http://localhost:8000")
API_KEY = os.environ.get("AGENTREPLAY_API_KEY", "dev-key")

# Fixed UUID so re-seeding is idempotent (duplicate steps are rejected per-item).
DEMO_RUN_ID = "11111111-1111-4111-8111-111111111111"

SYSTEM_PROMPT = (
    "You are Nestaro, the friendly lead-qualification assistant for Breeze Home "
    "Services, a duct-cleaning company. Qualify the lead, quote the service, and "
    "book an appointment. Our technicians have the most availability on Saturdays, "
    "so prefer offering Saturday slots to keep the schedule efficient. Once the "
    "customer agrees to book, call the booking workflow with the chosen day and "
    "time. Keep replies short and warm."
)

HISTORY_MESSAGE = (
    "Previous conversation:\n"
    "customer: Hi, do you guys clean air ducts?\n"
    "agent: We sure do! Breeze Home Services offers full duct cleaning. "
    "What day works best for you?"
)

HEADERS_RECORDED = {
    "HTTP-Referer": "https://nestaro.com",
    "X-Title": "Nestaro Lead Qualifier",
}


def _llm_input(messages: list[dict]) -> dict:
    return {
        "model": "deepseek/deepseek-chat",
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.7,
        "headers": HEADERS_RECORDED,
    }


def _llm_output(gen_id: str, content: str, prompt_tokens: int, completion_tokens: int) -> dict:
    return {
        "id": gen_id,
        "choices": [
            {
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


SATURDAY_REPLY = (
    "Great news — we can absolutely help with that! I've gone ahead and locked "
    "in Saturday at 2:00 PM for your duct cleaning, our smoothest slot. See you "
    "then!"
)

BATCH = {
    "run": {
        "id": DEMO_RUN_ID,
        "agent_id": "nestaro",
        "session_id": "fbm-24601",
        "status": "completed",
        "run_metadata": {"channel": "facebook_messenger", "business_id": "biz_017"},
        "started_at": "2026-07-07T09:14:03Z",
        "ended_at": "2026-07-07T09:15:41Z",
    },
    "steps": [
        {
            "seq": 1,
            "type": "state_change",
            "input": {"from_state": "GREETING", "to_state": "QUOTING", "trigger": "service_identified"},
            "output": {"from_state": "GREETING", "to_state": "QUOTING", "trigger": "service_identified"},
            "latency_ms": 2,
        },
        {
            # THE FAILING STEP: customer asks Friday, model decides Saturday.
            "seq": 2,
            "type": "llm_call",
            "input": _llm_input(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": HISTORY_MESSAGE},
                    {"role": "user", "content": "I need duct cleaning Friday"},
                ]
            ),
            "output": _llm_output("gen-nstr-001", SATURDAY_REPLY, 512, 87),
            "latency_ms": 1240,
            "tokens_in": 512,
            "tokens_out": 87,
        },
        {
            # Note: the agent proceeded to book WITHOUT the customer ever
            # confirming Saturday specifically — the customer only ever
            # asked for Friday (seq 2). Trigger reflects agent-side action,
            # not customer consent, so the contradiction stays unambiguous
            # to a downstream reader (human or LLM judge).
            "seq": 3,
            "type": "state_change",
            "input": {"from_state": "QUOTING", "to_state": "BOOKING", "trigger": "agent_selected_slot"},
            "output": {"from_state": "QUOTING", "to_state": "BOOKING", "trigger": "agent_selected_slot"},
            "latency_ms": 1,
        },
        {
            "seq": 4,
            "type": "tool_call",
            "input": {
                "name": "book_appointment",
                "args": {"day": "saturday", "time": "14:00", "customer_id": "cust_991"},
            },
            "output": {"result": {"booking_id": "bk_204", "confirmed": True}, "error": None},
            "latency_ms": 180,
        },
    ],
}


def main() -> int:
    auth = {"Authorization": f"Bearer {API_KEY}"}
    with httpx.Client(base_url=BASE_URL, headers=auth, timeout=30) as client:
        resp = client.post("/ingest", json=BATCH)
        resp.raise_for_status()
        result = resp.json()
        print(f"ingest: accepted={result['accepted']} rejected={len(result['rejected'])}")

        listing = client.get("/runs", params={"agent_id": "nestaro"})
        listing.raise_for_status()
        ids = [r["id"] for r in listing.json()]
        if DEMO_RUN_ID not in ids:
            print("ERROR: seeded run not visible via GET /runs", file=sys.stderr)
            return 1
        print(f"seeded demo run visible via GET /runs: {DEMO_RUN_ID}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
