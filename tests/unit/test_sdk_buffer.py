"""Unit tests for the SDK's in-memory event buffer (FR-003, FR-004).

No network involved — pure buffer/batch-shaping logic.
"""

from agentreplay.buffer import Buffer


def _new_buffer() -> Buffer:
    return Buffer(
        run_id="11111111-1111-4111-8111-111111111111",
        agent_id="nestaro",
        session_id="sess-1",
        run_metadata={"channel": "test"},
        started_at="2026-07-09T10:00:00Z",
    )


def test_buffer_assigns_contiguous_1_based_seq():
    buf = _new_buffer()
    seq1 = buf.add_step("state_change", {"from_state": "A", "to_state": "B", "trigger": "t"}, {"from_state": "A", "to_state": "B", "trigger": "t"})
    seq2 = buf.add_step("llm_call", {"model": "x"}, {"id": "y"})
    seq3 = buf.add_step("tool_call", {"name": "book"}, {"result": {}, "error": None})
    assert (seq1, seq2, seq3) == (1, 2, 3)


def test_buffer_accumulates_events_before_drain():
    buf = _new_buffer()
    buf.add_step("state_change", {}, {})
    buf.add_step("llm_call", {}, {})
    assert buf.pending_count() == 2


def test_drain_produces_ingest_batch_shape():
    buf = _new_buffer()
    buf.add_step(
        "llm_call",
        {"model": "deepseek/deepseek-chat"},
        {"id": "gen-1"},
        latency_ms=120,
        tokens_in=50,
        tokens_out=10,
    )
    batch = buf.drain()

    assert set(batch.keys()) == {"run", "steps"}
    assert batch["run"]["id"] == "11111111-1111-4111-8111-111111111111"
    assert batch["run"]["agent_id"] == "nestaro"
    assert batch["run"]["session_id"] == "sess-1"
    assert batch["run"]["status"] == "running"
    assert batch["run"]["run_metadata"] == {"channel": "test"}
    assert batch["run"]["started_at"] == "2026-07-09T10:00:00Z"
    assert batch["run"]["ended_at"] is None

    assert len(batch["steps"]) == 1
    step = batch["steps"][0]
    assert step["seq"] == 1
    assert step["type"] == "llm_call"
    assert step["input"] == {"model": "deepseek/deepseek-chat"}
    assert step["output"] == {"id": "gen-1"}
    assert step["latency_ms"] == 120
    assert step["tokens_in"] == 50
    assert step["tokens_out"] == 10


def test_drain_empties_pending_steps_but_keeps_seq_counter():
    buf = _new_buffer()
    buf.add_step("state_change", {}, {})
    first = buf.drain()
    assert len(first["steps"]) == 1

    second = buf.drain()
    assert second["steps"] == []

    # seq counter is NOT reset by drain — the next event continues from seq 2
    seq = buf.add_step("state_change", {}, {})
    assert seq == 2


def test_finalize_sets_status_and_ended_at():
    buf = _new_buffer()
    buf.finalize(status="completed", ended_at="2026-07-09T10:05:00Z")
    batch = buf.drain()
    assert batch["run"]["status"] == "completed"
    assert batch["run"]["ended_at"] == "2026-07-09T10:05:00Z"
