"""Dedicated US4 safety-contract tests: temperature policy (AS-2/3) and
parent immutability (AS-4, SC-005) — exercised in isolation from US1's
demo-narrative fork tests (test_fork.py), per research R4's generality
guarantee. Overlap with test_fork.py is intentional.
"""

import json
import os
import uuid

import httpx
import respx


def _replay_base_url() -> str:
    os.environ["REPLAY_BASE_URL"] = "https://replay-safety.test/v1"
    return os.environ["REPLAY_BASE_URL"]


def _seed_parent(client, auth_headers) -> str:
    run_id = str(uuid.uuid4())
    batch = {
        "run": {
            "id": run_id,
            "agent_id": "nestaro",
            "session_id": "sess-fork-safety",
            "status": "flagged",
            "run_metadata": {"detection": {"verdict": "fail", "reason": "x"}},
            "started_at": "2026-07-09T10:00:00Z",
            "ended_at": "2026-07-09T10:01:00Z",
        },
        "steps": [
            {
                "seq": 1,
                "type": "llm_call",
                "input": {
                    "model": "deepseek/deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are Nestaro."},
                        {"role": "user", "content": "I need duct cleaning Friday"},
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7,
                    "headers": {"HTTP-Referer": "https://nestaro.com", "X-Title": "Nestaro"},
                },
                "output": {
                    "id": "gen-1",
                    "choices": [{"message": {"role": "assistant", "content": "Booking Saturday."}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 50, "completion_tokens": 10},
                },
                "tokens_in": 50,
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
    return run_id


def _capturing_mock(captured: list[dict], content: str = "ok"):
    def _side_effect(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        return _mock_llm_response(content)

    return _side_effect


def _mock_llm_response(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "gen-fork",
            "choices": [{"message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 40, "completion_tokens": 8},
        },
    )


@respx.mock
def test_fork_defaults_to_temperature_zero_when_not_overridden(client, auth_headers):
    base_url = _replay_base_url()
    run_id = _seed_parent(client, auth_headers)

    captured: list[dict] = []
    respx.post(f"{base_url}/chat/completions").mock(side_effect=_capturing_mock(captured))

    resp = client.post(
        f"/runs/{run_id}/fork",
        json={"fork_step": 1, "modification": {"system_prompt": "fixed"}},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    fork = resp.json()

    assert fork["steps"][0]["input"]["temperature"] == 0
    assert captured[0]["temperature"] == 0


@respx.mock
def test_fork_honors_explicit_temperature_override(client, auth_headers):
    base_url = _replay_base_url()
    run_id = _seed_parent(client, auth_headers)

    captured: list[dict] = []
    respx.post(f"{base_url}/chat/completions").mock(side_effect=_capturing_mock(captured))

    for override in (0.3, 1.0, 2.0):
        captured.clear()
        resp = client.post(
            f"/runs/{run_id}/fork",
            json={"fork_step": 1, "modification": {"system_prompt": "fixed"}, "temperature": override},
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        fork = resp.json()
        assert fork["steps"][0]["input"]["temperature"] == override
        assert captured[0]["temperature"] == override


@respx.mock
def test_parent_run_and_steps_are_byte_for_byte_unchanged_after_fork(client, auth_headers):
    base_url = _replay_base_url()
    run_id = _seed_parent(client, auth_headers)

    respx.post(f"{base_url}/chat/completions").mock(return_value=_mock_llm_response("ok"))

    before = client.get(f"/runs/{run_id}", headers=auth_headers).json()

    for _ in range(3):  # multiple forks off the same parent — still never mutated
        resp = client.post(
            f"/runs/{run_id}/fork",
            json={"fork_step": 1, "modification": {"system_prompt": "fixed"}},
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text

    after = client.get(f"/runs/{run_id}", headers=auth_headers).json()
    assert before == after
    assert len(after["steps"]) == 2  # still exactly the 2 originally recorded steps


@respx.mock
def test_fork_never_creates_a_tool_call_step(client, auth_headers):
    """Single-shot fork (research R4): exactly one llm_call step, zero tool_call
    steps — the interceptor's typed-mock/positional/hash tiers are simply
    never reached on this path (constitution III's guarantee holds vacuously
    here; test_interception_tiers.py proves it holds when exercised directly)."""
    base_url = _replay_base_url()
    run_id = _seed_parent(client, auth_headers)

    respx.post(f"{base_url}/chat/completions").mock(return_value=_mock_llm_response("ok"))

    resp = client.post(
        f"/runs/{run_id}/fork",
        json={"fork_step": 1, "modification": {"system_prompt": "fixed"}},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    fork = resp.json()

    assert len(fork["steps"]) == 1
    assert all(s["type"] != "tool_call" for s in fork["steps"])
