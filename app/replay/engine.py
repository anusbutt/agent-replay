"""Single-shot fork execution (constitution I/II/IV; research R4/R6).

A fork executes exactly ONE live llm_call at the fork step:
  1. Load parent steps 1..fork_step.
  2. Reconstruct the recorded llm_call.input at (or nearest at-or-before) the
     fork step.
  3. Apply the modification (system_prompt replacement).
  4. Call the model live ONCE at temperature 0 (unless overridden) via
     REPLAY_BASE_URL, reusing the recorded `model` id (research R6).
  5. Record that single new llm_call step (seq 1) on a NEW run with
     parent_run_id + fork_step set, agent_id/session_id copied from parent.

Does NOT walk subsequent parent steps, re-issue later llm_calls, reconstruct
Nestaro's "Previous conversation" history format, or re-execute agent code.
"""

import copy
import os
import uuid
from datetime import UTC, datetime

import httpx
from sqlmodel import Session, select

from app.models import Run, RunStatus, Step, StepType


class ForkValidationError(Exception):
    """No reconstructable llm_call context at-or-before the requested fork_step."""


class ForkExecutionError(Exception):
    """The live replay model call failed."""


def _nearest_llm_call_at_or_before(steps: list[Step], fork_step: int) -> Step:
    candidates = [s for s in steps if s.type == StepType.llm_call and s.seq <= fork_step]
    if not candidates:
        raise ForkValidationError(
            f"no reconstructable llm_call context at or before fork_step={fork_step}"
        )
    return max(candidates, key=lambda s: s.seq)


def _apply_modification(llm_input: dict, modification: dict) -> dict:
    """Apply the user's modification to the reconstructed llm_call.input.

    V1 supports replacing the system message content (the primary acceptance
    scenario's fix). Unknown modification keys are ignored — additive room
    for future modification types without breaking the contract.
    """
    reconstructed = copy.deepcopy(llm_input)
    system_prompt = modification.get("system_prompt")
    if system_prompt is not None:
        messages = reconstructed.get("messages", [])
        for msg in messages:
            if msg.get("role") == "system":
                msg["content"] = system_prompt
                break
        else:
            messages.insert(0, {"role": "system", "content": system_prompt})
        reconstructed["messages"] = messages
    return reconstructed


def _call_replay_model(llm_input: dict) -> dict:
    """Execute exactly one live model call via REPLAY_BASE_URL (research R6)."""
    base_url = os.environ.get("REPLAY_BASE_URL", "https://openrouter.ai/api/v1")
    api_key = os.environ.get("REPLAY_API_KEY", "")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body = {
        "model": llm_input["model"],
        "messages": llm_input["messages"],
        "temperature": llm_input["temperature"],
    }
    if "max_tokens" in llm_input:
        body["max_tokens"] = llm_input["max_tokens"]

    try:
        resp = httpx.post(f"{base_url}/chat/completions", json=body, headers=headers, timeout=60)
    except httpx.HTTPError as exc:
        raise ForkExecutionError(f"replay endpoint unreachable: {exc}") from exc

    if resp.status_code >= 400:
        raise ForkExecutionError(f"replay endpoint returned {resp.status_code}: {resp.text}")

    return resp.json()


def execute_fork(
    session: Session,
    *,
    parent: Run,
    fork_step: int,
    modification: dict,
    temperature: float | None,
) -> Run:
    """Execute the single-shot fork and persist the new run + its one step.

    Raises ForkValidationError before any run is created if fork_step has no
    reconstructable llm_call context. On a live-call failure, the fork run is
    still created and marked `failed` (audit trail of the attempt) and
    ForkExecutionError propagates to the caller.
    """
    parent_steps = list(
        session.exec(select(Step).where(Step.run_id == parent.id).order_by(Step.seq)).all()
    )
    base_step = _nearest_llm_call_at_or_before(parent_steps, fork_step)

    resolved_temperature = 0 if temperature is None else temperature
    reconstructed_input = _apply_modification(base_step.input, modification)
    reconstructed_input["temperature"] = resolved_temperature

    fork_run = Run(
        id=uuid.uuid4(),
        agent_id=parent.agent_id,
        session_id=parent.session_id,
        status=RunStatus.running,
        parent_run_id=parent.id,
        fork_step=fork_step,
        run_metadata={},
        started_at=datetime.now(UTC),
    )
    session.add(fork_run)
    session.flush()

    try:
        raw_response = _call_replay_model(reconstructed_input)
    except ForkExecutionError:
        fork_run.status = RunStatus.failed
        fork_run.ended_at = datetime.now(UTC)
        session.add(fork_run)
        session.commit()
        raise

    session.add(
        Step(
            run_id=fork_run.id,
            seq=1,
            type=StepType.llm_call,
            input=reconstructed_input,
            output=raw_response,
            tokens_in=raw_response.get("usage", {}).get("prompt_tokens"),
            tokens_out=raw_response.get("usage", {}).get("completion_tokens"),
        )
    )
    fork_run.status = RunStatus.completed
    fork_run.ended_at = datetime.now(UTC)
    session.add(fork_run)
    session.commit()
    session.refresh(fork_run)

    return fork_run
