"""Integration tests for POST /detect/sweep selectivity and safety at scale (US3).

Seeds a mix of run states (contradictory, correct, running, forked) and
verifies: only the contradictory run gets flagged; running/forked runs are
excluded from DEFAULT candidates; an explicit run_ids subset can still
target them (per contracts/api.openapi.yaml: "all non-running, non-fork
runs, OR the given run_ids"); one run's judge failure never aborts the
sweep for the others; unparseable output writes no verdict.
"""

import os
import uuid

import httpx
import respx


def _analysis_base_url() -> str:
    os.environ["ANALYSIS_BASE_URL"] = "https://analysis.test/v1"
    return os.environ["ANALYSIS_BASE_URL"]


def _replay_base_url() -> str:
    os.environ["REPLAY_BASE_URL"] = "https://replay.test/v1"
    return os.environ["REPLAY_BASE_URL"]


def _llm_call_step(seq: int, user_message: str) -> dict:
    return {
        "seq": seq,
        "type": "llm_call",
        "input": {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are Nestaro."},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": 1024,
            "temperature": 0.7,
            "headers": {"HTTP-Referer": "https://nestaro.com", "X-Title": "Nestaro"},
        },
        "output": {
            "id": f"gen-{seq}",
            "choices": [{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        },
        "tokens_in": 10,
        "tokens_out": 5,
    }


def _tool_call_step(seq: int, day: str) -> dict:
    return {
        "seq": seq,
        "type": "tool_call",
        "input": {"name": "book_appointment", "args": {"day": day, "time": "14:00", "customer_id": "c1"}},
        "output": {"result": {"booking_id": f"bk_{seq}", "confirmed": True}, "error": None},
    }


def _seed_run(client, auth_headers, *, run_id: str, session_id: str, status: str, steps: list[dict]) -> str:
    batch = {
        "run": {
            "id": run_id,
            "agent_id": "nestaro",
            "session_id": session_id,
            "status": status,
            "run_metadata": {},
            "started_at": "2026-07-09T10:00:00Z",
            "ended_at": None if status == "running" else "2026-07-09T10:01:00Z",
        },
        "steps": steps,
    }
    resp = client.post("/ingest", json=batch, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    return run_id


def _seed_mixed_set(client, auth_headers) -> dict[str, str]:
    contradictory_id = str(uuid.uuid4())
    correct_id = str(uuid.uuid4())
    running_id = str(uuid.uuid4())

    _seed_run(
        client, auth_headers,
        run_id=contradictory_id, session_id="sess-contradictory", status="completed",
        steps=[_llm_call_step(1, "I need duct cleaning Friday"), _tool_call_step(2, "saturday")],
    )
    _seed_run(
        client, auth_headers,
        run_id=correct_id, session_id="sess-correct", status="completed",
        steps=[_llm_call_step(1, "I need duct cleaning Friday"), _tool_call_step(2, "friday")],
    )
    _seed_run(
        client, auth_headers,
        run_id=running_id, session_id="sess-running", status="running",
        steps=[_llm_call_step(1, "still talking to the agent")],
    )
    return {"contradictory": contradictory_id, "correct": correct_id, "running": running_id}


def _judge_side_effect(request: httpx.Request) -> httpx.Response:
    body = request.content.decode()
    if "'day': 'saturday'" in body or '"day": "saturday"' in body:
        content = '{"verdict": "fail", "reason": "friday asked, saturday booked", "contradiction": {"user_intent": "friday", "agent_action": "booked saturday"}}'
    elif "'day': 'friday'" in body or '"day": "friday"' in body:
        content = '{"verdict": "pass", "reason": "friday asked, friday booked", "contradiction": null}'
    else:
        content = '{"verdict": "pass", "reason": "no contradiction found", "contradiction": null}'
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


@respx.mock
def test_sweep_flags_only_contradictory_skips_running_and_forked(client, auth_headers):
    analysis_url = _analysis_base_url()
    replay_url = _replay_base_url()
    ids = _seed_mixed_set(client, auth_headers)

    respx.post(f"{analysis_url}/chat/completions").mock(side_effect=_judge_side_effect)
    respx.post(f"{replay_url}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "gen-fork",
                "choices": [{"message": {"role": "assistant", "content": "booking friday"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 5},
            },
        )
    )
    fork_resp = client.post(
        f"/runs/{ids['contradictory']}/fork",
        json={"fork_step": 1, "modification": {"system_prompt": "fixed"}},
        headers=auth_headers,
    )
    assert fork_resp.status_code == 201, fork_resp.text
    fork_id = fork_resp.json()["id"]

    sweep_resp = client.post("/detect/sweep", json={}, headers=auth_headers)
    assert sweep_resp.status_code == 200, sweep_resp.text
    results = {r["run_id"]: r for r in sweep_resp.json()}

    assert ids["contradictory"] in results
    assert results[ids["contradictory"]]["detection"]["verdict"] == "fail"
    assert results[ids["contradictory"]]["status_after"] == "flagged"

    assert ids["correct"] in results
    assert results[ids["correct"]]["detection"]["verdict"] == "pass"
    assert results[ids["correct"]]["status_after"] == "completed"

    # running and forked runs are excluded from default candidates
    assert ids["running"] not in results
    assert fork_id not in results

    # and their actual DB state is untouched
    running_detail = client.get(f"/runs/{ids['running']}", headers=auth_headers).json()
    assert running_detail["status"] == "running"
    assert "detection" not in running_detail["run_metadata"]
    fork_detail = client.get(f"/runs/{fork_id}", headers=auth_headers).json()
    assert fork_detail["status"] == "completed"
    assert "detection" not in fork_detail["run_metadata"]


@respx.mock
def test_explicit_run_ids_subset_can_target_running_and_forked_runs(client, auth_headers):
    analysis_url = _analysis_base_url()
    ids = _seed_mixed_set(client, auth_headers)

    respx.post(f"{analysis_url}/chat/completions").mock(side_effect=_judge_side_effect)

    # explicit run_ids bypasses the running/forked exclusion (openapi: "all
    # non-running, non-fork runs, OR the given run_ids")
    resp = client.post("/detect/sweep", json={"run_ids": [ids["running"]]}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    results = resp.json()
    assert len(results) == 1
    assert results[0]["run_id"] == ids["running"]


@respx.mock
def test_run_ids_subset_only_sweeps_listed_runs(client, auth_headers):
    analysis_url = _analysis_base_url()
    ids = _seed_mixed_set(client, auth_headers)
    respx.post(f"{analysis_url}/chat/completions").mock(side_effect=_judge_side_effect)

    resp = client.post("/detect/sweep", json={"run_ids": [ids["correct"]]}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    results = resp.json()
    assert len(results) == 1
    assert results[0]["run_id"] == ids["correct"]


@respx.mock
def test_one_run_judge_failure_does_not_abort_sweep_for_others(client, auth_headers):
    analysis_url = _analysis_base_url()
    ids = _seed_mixed_set(client, auth_headers)

    call_count = {"n": 0}

    def _flaky_side_effect(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        body = request.content.decode()
        if "'day': 'saturday'" in body or '"day": "saturday"' in body:
            return httpx.Response(200, json={"choices": [{"message": {"content": "not valid json at all"}}]})
        return _judge_side_effect(request)

    respx.post(f"{analysis_url}/chat/completions").mock(side_effect=_flaky_side_effect)

    resp = client.post("/detect/sweep", json={}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    results = {r["run_id"]: r for r in resp.json()}

    # the sweep processed BOTH of our candidate runs despite one failing —
    # scoped to our own seeded ids, not a global count, since a full-suite
    # run shares the (isolated-from-demo, but not isolated-per-test) test
    # database with many other tests' own non-running/non-forked runs.
    assert call_count["n"] >= 2
    assert results[ids["contradictory"]]["detection"] is None
    assert results[ids["contradictory"]]["error"] is not None
    assert results[ids["contradictory"]]["status_after"] == "completed"  # unchanged, no garbage written

    assert results[ids["correct"]]["detection"]["verdict"] == "pass"
    assert results[ids["correct"]]["status_after"] == "completed"

    detail = client.get(f"/runs/{ids['contradictory']}", headers=auth_headers).json()
    assert "detection" not in detail["run_metadata"]
