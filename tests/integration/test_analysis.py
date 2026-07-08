"""Integration tests for POST /runs/{run_id}/analyze (FR-019, FR-020, SC-007).

Uses respx to stub the OpenAI-compatible ANALYSIS_BASE_URL endpoint.
"""

import os
import uuid

import httpx
import respx


def _analysis_base_url() -> str:
    # Force-set (not setdefault) — a container env may already set this to ""
    # via compose's ${VAR:-} default, which setdefault would leave in place,
    # desyncing the mock target from what the app actually calls.
    os.environ["ANALYSIS_BASE_URL"] = "https://analysis.test/v1"
    return os.environ["ANALYSIS_BASE_URL"]


def _seed_run(client, auth_headers) -> str:
    run_id = str(uuid.uuid4())
    batch = {
        "run": {
            "id": run_id,
            "agent_id": "nestaro",
            "session_id": "sess-analyze",
            "status": "flagged",
            "run_metadata": {"detection": {"verdict": "fail", "reason": "friday vs saturday"}},
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
                    "choices": [{"message": {"role": "assistant", "content": "Booking Saturday."}, "finish_reason": "stop"}],
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


@respx.mock
def test_analyze_stores_verdict_naming_existing_failing_step(client, auth_headers):
    base_url = _analysis_base_url()
    run_id = _seed_run(client, auth_headers)

    respx.post(f"{base_url}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"failing_step": 1, "root_cause": '
                                '"System prompt never confirms the requested day.", '
                                '"suggested_fix": "Always book the exact day requested."}'
                            )
                        }
                    }
                ]
            },
        )
    )

    resp = client.post(f"/runs/{run_id}/analyze", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["failing_step"] == 1
    assert body["root_cause"]
    assert body["suggested_fix"]

    detail = client.get(f"/runs/{run_id}", headers=auth_headers).json()
    assert detail["run_metadata"]["analysis"]["failing_step"] == 1
    step_seqs = {s["seq"] for s in detail["steps"]}
    assert detail["run_metadata"]["analysis"]["failing_step"] in step_seqs
    # detection verdict from before analyze must survive untouched
    assert detail["run_metadata"]["detection"]["verdict"] == "fail"


@respx.mock
def test_analyze_model_failure_returns_502_and_run_unchanged(client, auth_headers):
    base_url = _analysis_base_url()
    run_id = _seed_run(client, auth_headers)

    respx.post(f"{base_url}/chat/completions").mock(return_value=httpx.Response(500, json={"error": "boom"}))

    resp = client.post(f"/runs/{run_id}/analyze", headers=auth_headers)
    assert resp.status_code == 502, resp.text

    detail = client.get(f"/runs/{run_id}", headers=auth_headers).json()
    assert "analysis" not in detail["run_metadata"]
    assert detail["status"] == "flagged"


def test_analyze_unknown_run_404(client, auth_headers):
    resp = client.post(f"/runs/{uuid.uuid4()}/analyze", headers=auth_headers)
    assert resp.status_code == 404
