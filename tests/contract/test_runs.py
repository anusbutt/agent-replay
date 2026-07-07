"""Contract tests for GET /runs and GET /runs/{run_id} (FR-010, FR-011 substrate)."""

import uuid


def _seed(client, auth_headers, agent_id: str, session_id: str = "sess-runs") -> str:
    run_id = str(uuid.uuid4())
    batch = {
        "run": {
            "id": run_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "status": "completed",
            "run_metadata": {},
            "started_at": "2026-07-07T10:00:00Z",
            "ended_at": "2026-07-07T10:01:00Z",
        },
        "steps": [
            {
                "seq": 2,
                "type": "state_change",
                "input": {"from_state": "A", "to_state": "B", "trigger": "t"},
                "output": {"from_state": "A", "to_state": "B", "trigger": "t"},
            },
            {
                "seq": 1,
                "type": "tool_call",
                "input": {"name": "noop", "args": {}},
                "output": {"result": {}, "error": None},
            },
        ],
    }
    resp = client.post("/ingest", json=batch, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    return run_id


def test_list_runs_with_filters_and_lineage_fields(client, auth_headers):
    agent_id = f"agent-{uuid.uuid4().hex[:8]}"
    run_id = _seed(client, auth_headers, agent_id)

    resp = client.get("/runs", params={"agent_id": agent_id}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    runs = resp.json()
    assert len(runs) == 1
    run = runs[0]
    assert run["id"] == run_id
    assert run["agent_id"] == agent_id
    assert run["session_id"] == "sess-runs"
    assert run["status"] == "completed"
    # Fork lineage fields are present (null for non-forks) — FR-012 substrate
    assert "parent_run_id" in run and run["parent_run_id"] is None
    assert "fork_step" in run and run["fork_step"] is None

    # status filter excludes it
    resp = client.get(
        "/runs", params={"agent_id": agent_id, "status": "flagged"}, headers=auth_headers
    )
    assert resp.json() == []


def test_run_detail_steps_ordered_by_seq(client, auth_headers):
    agent_id = f"agent-{uuid.uuid4().hex[:8]}"
    run_id = _seed(client, auth_headers, agent_id)

    resp = client.get(f"/runs/{run_id}", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    detail = resp.json()
    # steps ingested out of order come back ordered by seq ascending
    assert [s["seq"] for s in detail["steps"]] == [1, 2]
    assert detail["steps"][0]["type"] == "tool_call"
    assert detail["steps"][1]["type"] == "state_change"
    for field in ("id", "run_id", "seq", "type", "input", "output"):
        assert field in detail["steps"][0]


def test_unknown_run_returns_404(client, auth_headers):
    resp = client.get(f"/runs/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


def test_runs_require_api_key(client):
    assert client.get("/runs").status_code == 401
