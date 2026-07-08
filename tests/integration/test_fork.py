"""Integration tests for POST /runs/{run_id}/fork (FR-014/15/17/18, SC-004/5, research R4).

Single-shot fork: exactly ONE live llm_call at the fork step, at temperature 0
unless overridden, zero real tool executions, parent immutable.
Uses respx to stub the OpenAI-compatible REPLAY_BASE_URL endpoint.
"""

import os
import uuid

import httpx
import respx


def _replay_base_url() -> str:
    # Force-set (not setdefault) — a container env may already set this to a
    # real endpoint, which setdefault would leave in place, desyncing the
    # mock target from what the app actually calls.
    os.environ["REPLAY_BASE_URL"] = "https://replay.test/v1"
    return os.environ["REPLAY_BASE_URL"]


def _seed_parent_run(client, auth_headers) -> tuple[str, dict]:
    run_id = str(uuid.uuid4())
    llm_input = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are Nestaro. Prefer Saturday slots."},
            {"role": "user", "content": "Previous conversation:\ncustomer: hi\nagent: hello"},
            {"role": "user", "content": "I need duct cleaning Friday"},
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
        "headers": {"HTTP-Referer": "https://nestaro.com", "X-Title": "Nestaro"},
    }
    batch = {
        "run": {
            "id": run_id,
            "agent_id": "nestaro",
            "session_id": "sess-fork",
            "status": "flagged",
            "run_metadata": {
                "detection": {"verdict": "fail", "reason": "friday vs saturday"},
                "analysis": {
                    "failing_step": 1,
                    "root_cause": "prompt biases toward Saturday",
                    "suggested_fix": "Always book the exact day requested.",
                },
            },
            "started_at": "2026-07-07T10:00:00Z",
            "ended_at": "2026-07-07T10:01:00Z",
        },
        "steps": [
            {
                "seq": 1,
                "type": "llm_call",
                "input": llm_input,
                "output": {
                    "id": "gen-1",
                    "choices": [{"message": {"role": "assistant", "content": "Booking Saturday 2pm."}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 100, "completion_tokens": 10},
                },
                "tokens_in": 100,
                "tokens_out": 10,
            },
            {
                "seq": 2,
                "type": "tool_call",
                "input": {"name": "book_appointment", "args": {"day": "saturday", "time": "14:00", "customer_id": "c1"}},
                "output": {"result": {"booking_id": "bk_1", "confirmed": True}, "error": None},
            },
        ],
    }
    resp = client.post("/ingest", json=batch, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    return run_id, llm_input


@respx.mock
def test_fork_creates_new_run_with_single_llm_call_at_temp_zero(client, auth_headers):
    base_url = _replay_base_url()
    run_id, parent_llm_input = _seed_parent_run(client, auth_headers)

    parent_before = client.get(f"/runs/{run_id}", headers=auth_headers).json()

    captured_requests: list[dict] = []

    def _capture(request: httpx.Request) -> httpx.Response:
        import json

        captured_requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "gen-fork-1",
                "choices": [{"message": {"role": "assistant", "content": "Booking Friday 10am."}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 90, "completion_tokens": 8},
            },
        )

    respx.post(f"{base_url}/chat/completions").mock(side_effect=_capture)

    fixed_prompt = "You are Nestaro. Always book the exact day requested."
    resp = client.post(
        f"/runs/{run_id}/fork",
        json={"fork_step": 1, "modification": {"system_prompt": fixed_prompt}},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    fork = resp.json()

    assert fork["id"] != run_id
    assert fork["parent_run_id"] == run_id
    assert fork["fork_step"] == 1
    assert fork["agent_id"] == "nestaro"
    assert fork["session_id"] == "sess-fork"
    assert len(fork["steps"]) == 1
    assert fork["steps"][0]["seq"] == 1
    assert fork["steps"][0]["type"] == "llm_call"
    assert fork["steps"][0]["input"]["temperature"] == 0
    assert fork["steps"][0]["input"]["messages"][0]["content"] == fixed_prompt
    # subsequent messages preserved from the reconstructed parent context
    assert fork["steps"][0]["input"]["messages"][1:] == parent_llm_input["messages"][1:]
    assert "friday" in fork["steps"][0]["output"]["choices"][0]["message"]["content"].lower()

    # exactly one live call was made, at temperature 0
    assert len(captured_requests) == 1
    assert captured_requests[0]["temperature"] == 0

    # parent run + steps byte-for-byte unchanged (constitution I)
    parent_after = client.get(f"/runs/{run_id}", headers=auth_headers).json()
    assert parent_after == parent_before


@respx.mock
def test_fork_temperature_override_is_honored(client, auth_headers):
    base_url = _replay_base_url()
    run_id, _ = _seed_parent_run(client, auth_headers)

    captured: list[dict] = []

    def _capture(request: httpx.Request) -> httpx.Response:
        import json

        captured.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "gen-fork-2",
                "choices": [{"message": {"role": "assistant", "content": "Booking Friday."}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 90, "completion_tokens": 8},
            },
        )

    respx.post(f"{base_url}/chat/completions").mock(side_effect=_capture)

    resp = client.post(
        f"/runs/{run_id}/fork",
        json={"fork_step": 1, "modification": {"system_prompt": "x"}, "temperature": 0.5},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["steps"][0]["input"]["temperature"] == 0.5
    assert captured[0]["temperature"] == 0.5


def test_fork_invalid_step_returns_422_and_creates_no_run(client, auth_headers):
    # A run whose fork_step has NO llm_call at-or-before it (only a leading
    # state_change) has no reconstructable LLM context — must fail per spec
    # edge case, not silently fork from nothing.
    run_id = str(uuid.uuid4())
    session_id = f"sess-fork-invalid-{uuid.uuid4().hex[:8]}"
    batch = {
        "run": {
            "id": run_id,
            "agent_id": "nestaro",
            "session_id": session_id,
            "status": "completed",
            "run_metadata": {},
            "started_at": "2026-07-07T10:00:00Z",
            "ended_at": "2026-07-07T10:01:00Z",
        },
        "steps": [
            {
                "seq": 1,
                "type": "state_change",
                "input": {"from_state": "GREETING", "to_state": "QUOTING", "trigger": "t"},
                "output": {"from_state": "GREETING", "to_state": "QUOTING", "trigger": "t"},
            }
        ],
    }
    resp = client.post("/ingest", json=batch, headers=auth_headers)
    assert resp.status_code == 200, resp.text

    resp = client.post(
        f"/runs/{run_id}/fork",
        json={"fork_step": 1, "modification": {"system_prompt": "x"}},
        headers=auth_headers,
    )
    assert resp.status_code == 422, resp.text

    runs = client.get("/runs", params={"agent_id": "nestaro", "session_id": session_id}, headers=auth_headers).json()
    assert len(runs) == 1  # only the parent — no fork run created
