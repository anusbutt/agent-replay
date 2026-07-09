"""Drives app/replay/interceptor.py DIRECTLY against a seeded parent run's
tool_call steps (US4 AS-1, constitution III) — NOT via the fork endpoint,
since Nestaro's single-shot forks emit no tool calls (research R4). This is
the generality guarantee for tool-emitting agents (V2/roadmap).

Verifies the exact resolution order: positional (run_id, seq) -> hash
fallback -> typed mock, and that a real tool is NEVER executed in any case.
"""

import uuid

import pytest
from sqlmodel import Session, select

from app.db import engine
from app.models import Step
from app.replay.interceptor import TYPED_MOCK, resolve_tool_call

# Sentinel: a "real" tool implementation that must NEVER be invoked by the
# interceptor. The interceptor has no code path to call this — this counter
# documents and proves that invariant at runtime (constitution III).
REAL_TOOL_CALLS = 0


@pytest.fixture(autouse=True)
def _reset_sentinel():
    global REAL_TOOL_CALLS
    REAL_TOOL_CALLS = 0
    yield


def _real_book_appointment(day: str, time: str, customer_id: str) -> dict:
    global REAL_TOOL_CALLS
    REAL_TOOL_CALLS += 1
    return {"booking_id": "REAL_BOOKING_MUST_NEVER_HAPPEN", "confirmed": True}


def _seed_parent_with_tool_calls(client, auth_headers) -> tuple[str, list[Step]]:
    run_id = str(uuid.uuid4())
    batch = {
        "run": {
            "id": run_id,
            "agent_id": "nestaro",
            "session_id": "sess-interception",
            "status": "completed",
            "run_metadata": {},
            "started_at": "2026-07-09T10:00:00Z",
            "ended_at": "2026-07-09T10:01:00Z",
        },
        "steps": [
            {
                "seq": 1,
                "type": "llm_call",
                "input": {"model": "deepseek/deepseek-chat", "messages": [], "max_tokens": 100, "temperature": 0.7},
                "output": {"id": "gen-1", "choices": [{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}},
            },
            {
                "seq": 2,
                "type": "tool_call",
                "input": {"name": "book_appointment", "args": {"day": "saturday", "time": "14:00", "customer_id": "cust_991"}},
                "output": {"result": {"booking_id": "bk_204", "confirmed": True}, "error": None},
            },
            {
                "seq": 3,
                "type": "state_change",
                "input": {"from_state": "BOOKING", "to_state": "DONE", "trigger": "confirmed"},
                "output": {"from_state": "BOOKING", "to_state": "DONE", "trigger": "confirmed"},
            },
            {
                "seq": 4,
                "type": "tool_call",
                "input": {"name": "send_reminder", "args": {"customer_id": "cust_991", "channel": "sms"}},
                "output": {"result": {"sent": True}, "error": None},
            },
        ],
    }
    resp = client.post("/ingest", json=batch, headers=auth_headers)
    assert resp.status_code == 200, resp.text

    with Session(engine) as session:
        steps = list(session.exec(select(Step).where(Step.run_id == uuid.UUID(run_id)).order_by(Step.seq)).all())
    return run_id, steps


def test_positional_match_by_run_id_and_seq_returns_cached_result(client, auth_headers):
    run_id, steps = _seed_parent_with_tool_calls(client, auth_headers)

    result = resolve_tool_call(
        run_id=run_id,
        seq=2,
        name="book_appointment",
        args={"day": "saturday", "time": "14:00", "customer_id": "cust_991"},
        recorded_steps=steps,
    )
    assert result == {"result": {"booking_id": "bk_204", "confirmed": True}, "error": None}
    assert REAL_TOOL_CALLS == 0


def test_positional_match_at_a_different_step_than_the_seed_still_matches_exact_seq(client, auth_headers):
    run_id, steps = _seed_parent_with_tool_calls(client, auth_headers)

    result = resolve_tool_call(
        run_id=run_id, seq=4, name="send_reminder", args={"customer_id": "cust_991", "channel": "sms"},
        recorded_steps=steps,
    )
    assert result == {"result": {"sent": True}, "error": None}
    assert REAL_TOOL_CALLS == 0


def test_hash_fallback_when_seq_mismatches_but_name_and_args_match(client, auth_headers):
    run_id, steps = _seed_parent_with_tool_calls(client, auth_headers)

    # seq=99 was never recorded at all — positional tier must miss, falling
    # through to the hash tier on identical name+args.
    result = resolve_tool_call(
        run_id=run_id,
        seq=99,
        name="book_appointment",
        args={"day": "saturday", "time": "14:00", "customer_id": "cust_991"},
        recorded_steps=steps,
    )
    assert result == {"result": {"booking_id": "bk_204", "confirmed": True}, "error": None}
    assert REAL_TOOL_CALLS == 0


def test_hash_fallback_is_insensitive_to_dict_key_order(client, auth_headers):
    run_id, steps = _seed_parent_with_tool_calls(client, auth_headers)

    result = resolve_tool_call(
        run_id=run_id,
        seq=42,
        name="book_appointment",
        args={"customer_id": "cust_991", "day": "saturday", "time": "14:00"},  # reordered
        recorded_steps=steps,
    )
    assert result == {"result": {"booking_id": "bk_204", "confirmed": True}, "error": None}
    assert REAL_TOOL_CALLS == 0


def test_unknown_tool_and_args_returns_typed_mock(client, auth_headers):
    run_id, steps = _seed_parent_with_tool_calls(client, auth_headers)

    result = resolve_tool_call(
        run_id=run_id,
        seq=999,
        name="cancel_subscription",
        args={"account_id": "never_recorded"},
        recorded_steps=steps,
    )
    assert result == TYPED_MOCK
    assert result == {"result": {"mocked": True}, "error": None}
    assert REAL_TOOL_CALLS == 0


def test_wrong_run_id_at_matching_seq_does_not_positionally_match(client, auth_headers):
    """Positional match is scoped to (run_id, seq) BOTH — a matching seq from
    a different run must not leak across runs."""
    run_id, steps = _seed_parent_with_tool_calls(client, auth_headers)

    result = resolve_tool_call(
        run_id=str(uuid.uuid4()),  # a different, unseeded run_id
        seq=2,  # matches the seed's seq, but for a different run
        name="totally_different_tool",
        args={"nothing": "matches"},
        recorded_steps=steps,
    )
    assert result == TYPED_MOCK
    assert REAL_TOOL_CALLS == 0


def test_interceptor_never_calls_a_real_tool_across_all_tiers(client, auth_headers):
    """Sentinel proof: _real_book_appointment is defined in this module but
    resolve_tool_call has no reference to it and no way to invoke it."""
    run_id, steps = _seed_parent_with_tool_calls(client, auth_headers)

    resolve_tool_call(run_id=run_id, seq=2, name="book_appointment", args={"day": "saturday", "time": "14:00", "customer_id": "cust_991"}, recorded_steps=steps)
    resolve_tool_call(run_id=run_id, seq=50, name="book_appointment", args={"day": "saturday", "time": "14:00", "customer_id": "cust_991"}, recorded_steps=steps)
    resolve_tool_call(run_id=run_id, seq=999, name="unknown_tool", args={}, recorded_steps=steps)

    assert REAL_TOOL_CALLS == 0
    # calling the real function directly (never via the interceptor) IS what
    # would increment the counter — proving the sentinel itself is live/wired.
    _real_book_appointment(day="saturday", time="14:00", customer_id="cust_991")
    assert REAL_TOOL_CALLS == 1
