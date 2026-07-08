"""Integration tests for POST /detect/sweep (FR-021, FR-022, research R5).

Uses respx to stub the OpenAI-compatible ANALYSIS_BASE_URL endpoint so no real
model call happens in tests.
"""

import os
import uuid

import httpx
import respx


def _seed_contradictory_run(client, auth_headers) -> str:
    run_id = str(uuid.uuid4())
    batch = {
        "run": {
            "id": run_id,
            "agent_id": "nestaro",
            "session_id": "sess-detect-fail",
            "status": "completed",
            "run_metadata": {},
            "started_at": "2026-07-07T10:00:00Z",
            "ended_at": "2026-07-07T10:01:00Z",
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
                    "max_tokens": 1024,
                    "temperature": 0.7,
                    "headers": {"HTTP-Referer": "https://nestaro.com", "X-Title": "Nestaro"},
                },
                "output": {
                    "id": "gen-1",
                    "choices": [
                        {"message": {"role": "assistant", "content": "Booking Saturday 2pm."}, "finish_reason": "stop"}
                    ],
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
    return run_id


def _analysis_base_url() -> str:
    # Force-set (not setdefault) — a container env may already set this to ""
    # via compose's ${VAR:-} default, which setdefault would leave in place,
    # desyncing the mock target from what the app actually calls.
    os.environ["ANALYSIS_BASE_URL"] = "https://analysis.test/v1"
    return os.environ["ANALYSIS_BASE_URL"]


@respx.mock
def test_sweep_flags_contradictory_run_and_stores_verdict(client, auth_headers):
    base_url = _analysis_base_url()
    run_id = _seed_contradictory_run(client, auth_headers)

    route = respx.post(f"{base_url}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"verdict": "fail", "reason": '
                                '"Customer asked Friday; agent booked Saturday.", '
                                '"contradiction": {"user_intent": "Friday", "agent_action": "booked saturday"}}'
                            )
                        }
                    }
                ]
            },
        )
    )

    resp = client.post("/detect/sweep", json={"run_ids": [run_id]}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert route.called
    results = resp.json()
    assert len(results) == 1
    assert results[0]["run_id"] == run_id
    assert results[0]["detection"]["verdict"] == "fail"
    assert results[0]["status_after"] == "flagged"

    detail = client.get(f"/runs/{run_id}", headers=auth_headers).json()
    assert detail["status"] == "flagged"
    assert detail["run_metadata"]["detection"]["verdict"] == "fail"
    assert detail["run_metadata"]["detection"]["contradiction"]["user_intent"] == "Friday"


@respx.mock
def test_sweep_unparseable_model_output_writes_nothing_and_reports_error(client, auth_headers):
    base_url = _analysis_base_url()
    run_id = _seed_contradictory_run(client, auth_headers)

    respx.post(f"{base_url}/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "not json at all"}}]})
    )

    resp = client.post("/detect/sweep", json={"run_ids": [run_id]}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    results = resp.json()
    assert len(results) == 1
    assert results[0]["run_id"] == run_id
    assert results[0]["detection"] is None
    assert results[0]["error"] is not None
    assert results[0]["status_after"] == "completed"  # unchanged — no verdict written

    detail = client.get(f"/runs/{run_id}", headers=auth_headers).json()
    assert detail["status"] == "completed"
    assert "detection" not in detail["run_metadata"]
