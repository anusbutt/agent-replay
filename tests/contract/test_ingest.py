"""Contract tests for POST /ingest (FR-007, FR-008, research R2).

Payload shapes are byte-identical to docs/DATA_CONTRACT.md — verbatim storage,
per-item rejection of duplicates/invalid steps, static-key auth.
"""

import uuid


def _llm_call_input() -> dict:
    return {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are Nestaro, a lead qualifier."},
            {"role": "user", "content": "Previous conversation:\ncustomer: hi\nagent: hello!"},
            {"role": "user", "content": "I need duct cleaning Friday"},
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
        "headers": {
            "HTTP-Referer": "https://nestaro.com",
            "X-Title": "Nestaro Lead Qualifier",
        },
    }


def _llm_call_output() -> dict:
    return {
        "id": "gen-abc123",
        "choices": [
            {
                "message": {"role": "assistant", "content": "I can book you Saturday at 14:00."},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 512, "completion_tokens": 87},
    }


def _batch(run_id: str) -> dict:
    return {
        "run": {
            "id": run_id,
            "agent_id": "nestaro-test",
            "session_id": "sess-contract",
            "status": "completed",
            "run_metadata": {"channel": "facebook_messenger"},
            "started_at": "2026-07-07T10:00:00Z",
            "ended_at": "2026-07-07T10:01:00Z",
        },
        "steps": [
            {
                "seq": 1,
                "type": "llm_call",
                "input": _llm_call_input(),
                "output": _llm_call_output(),
                "latency_ms": 950,
                "tokens_in": 512,
                "tokens_out": 87,
            },
            {
                "seq": 2,
                "type": "tool_call",
                "input": {
                    "name": "book_appointment",
                    "args": {"day": "saturday", "time": "14:00", "customer_id": "cust_991"},
                },
                "output": {"result": {"booking_id": "bk_204", "confirmed": True}, "error": None},
                "latency_ms": 120,
            },
            {
                "seq": 3,
                "type": "state_change",
                "input": {"from_state": "QUOTING", "to_state": "BOOKING", "trigger": "user_confirmed"},
                "output": {"from_state": "QUOTING", "to_state": "BOOKING", "trigger": "user_confirmed"},
            },
        ],
    }


def test_valid_batch_persists_verbatim_payloads(client, auth_headers):
    run_id = str(uuid.uuid4())
    batch = _batch(run_id)

    resp = client.post("/ingest", json=batch, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["run_id"] == run_id
    assert body["accepted"] == 3
    assert body["rejected"] == []

    detail = client.get(f"/runs/{run_id}", headers=auth_headers).json()
    assert detail["status"] == "completed"
    steps = detail["steps"]
    assert [s["seq"] for s in steps] == [1, 2, 3]
    assert [s["type"] for s in steps] == ["llm_call", "tool_call", "state_change"]
    # Verbatim — recorded payloads come back exactly as sent (FR-002 / data contract)
    assert steps[0]["input"] == _llm_call_input()
    assert steps[0]["output"] == _llm_call_output()
    assert steps[0]["tokens_in"] == 512
    assert steps[0]["tokens_out"] == 87
    assert steps[0]["latency_ms"] == 950
    assert steps[1]["input"] == batch["steps"][1]["input"]
    assert steps[1]["output"] == batch["steps"][1]["output"]
    assert steps[2]["input"] == batch["steps"][2]["input"]


def test_duplicate_seq_rejected_per_item_while_valid_items_persist(client, auth_headers):
    run_id = str(uuid.uuid4())
    first = _batch(run_id)
    assert client.post("/ingest", json=first, headers=auth_headers).status_code == 200

    retry = {
        "run": first["run"],
        "steps": [
            first["steps"][1],  # duplicate seq 2
            {
                "seq": 4,
                "type": "state_change",
                "input": {"from_state": "BOOKING", "to_state": "DONE", "trigger": "booked"},
                "output": {"from_state": "BOOKING", "to_state": "DONE", "trigger": "booked"},
            },
        ],
    }
    resp = client.post("/ingest", json=retry, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["accepted"] == 1
    assert len(body["rejected"]) == 1
    assert body["rejected"][0]["seq"] == 2

    detail = client.get(f"/runs/{run_id}", headers=auth_headers).json()
    assert [s["seq"] for s in detail["steps"]] == [1, 2, 3, 4]


def test_invalid_step_type_rejected_per_item(client, auth_headers):
    run_id = str(uuid.uuid4())
    batch = _batch(run_id)
    batch["steps"] = [
        batch["steps"][0],
        {"seq": 2, "type": "bogus_type", "input": {}, "output": {}},
    ]
    resp = client.post("/ingest", json=batch, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["accepted"] == 1
    assert len(body["rejected"]) == 1
    assert body["rejected"][0]["seq"] == 2
    assert "type" in body["rejected"][0]["error"]

    detail = client.get(f"/runs/{run_id}", headers=auth_headers).json()
    assert [s["seq"] for s in detail["steps"]] == [1]


def test_missing_or_wrong_api_key_returns_401(client, auth_headers):
    run_id = str(uuid.uuid4())
    batch = _batch(run_id)

    assert client.post("/ingest", json=batch).status_code == 401
    assert (
        client.post("/ingest", json=batch, headers={"Authorization": "Bearer wrong-key"}).status_code
        == 401
    )
    # And nothing was persisted for that run
    resp = client.get(f"/runs/{run_id}", headers=auth_headers)
    assert resp.status_code == 404
