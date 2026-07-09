"""Integration tests: the SDK must never raise into host agent code (FR-005, SC-003,
constitution V), even when the transport target is completely unreachable or
actively erroring. Errors are swallowed and logged locally only.
"""

import httpx
import respx

import agentreplay as replay


class _FakeChatCompletion:
    def __init__(self):
        self.id = "gen-1"
        self.choices = [
            type("C", (), {"message": type("M", (), {"role": "assistant", "content": "ok"})(), "finish_reason": "stop"})()
        ]
        self.usage = type("U", (), {"prompt_tokens": 1, "completion_tokens": 1})()

    def model_dump(self):
        return {
            "id": self.id,
            "choices": [{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }


class _FakeCompletions:
    def create(self, **kwargs):
        return _FakeChatCompletion()


class _FakeChat:
    def __init__(self):
        self.completions = _FakeCompletions()


class _FakeClient:
    def __init__(self):
        self.chat = _FakeChat()


@replay.tool
def book_appointment(day: str, time: str, customer_id: str):
    return {"booking_id": "bk_1", "confirmed": True}


def test_full_flow_completes_without_raising_against_dead_port():
    # Port 1 is a privileged, virtually always-closed port — guarantees a
    # real connection-refused error, not a mock.
    replay.init(base_url="http://127.0.0.1:1", api_key="k", agent_id="dead-port-test")

    wrapped = replay.wrap(_FakeClient())
    result = wrapped.chat.completions.create(model="x", messages=[{"role": "user", "content": "hi"}])
    assert result.id == "gen-1"  # the wrapped call itself still behaves normally

    tool_result = book_appointment(day="friday", time="10:00", customer_id="c1")
    assert tool_result == {"booking_id": "bk_1", "confirmed": True}

    replay.record_state_change("A", "B", "trigger")

    # flush() and end_run() both attempt network I/O against the dead port —
    # neither must raise.
    replay.flush()
    replay.end_run(status="completed")


@respx.mock
def test_full_flow_completes_without_raising_against_erroring_server():
    respx.post("http://erroring-server.invalid/ingest").mock(
        return_value=httpx.Response(500, json={"detail": "boom"})
    )
    replay.init(base_url="http://erroring-server.invalid", api_key="k", agent_id="erroring-server-test")

    wrapped = replay.wrap(_FakeClient())
    wrapped.chat.completions.create(model="x", messages=[{"role": "user", "content": "hi"}])
    book_appointment(day="friday", time="10:00", customer_id="c1")
    replay.record_state_change("A", "B", "trigger")

    replay.flush()
    replay.end_run(status="completed")


def test_wrap_and_tool_are_no_ops_before_init_and_never_raise():
    # Simulate a host that forgot to call init() — recording must be
    # invisible, not crash the host.
    replay._state = None  # noqa: SLF001 — test-only reset

    wrapped = replay.wrap(_FakeClient())
    result = wrapped.chat.completions.create(model="x", messages=[])
    assert result.id == "gen-1"

    tool_result = book_appointment(day="friday", time="10:00", customer_id="c1")
    assert tool_result == {"booking_id": "bk_1", "confirmed": True}

    replay.record_state_change("A", "B", "trigger")
    replay.flush()
