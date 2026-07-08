"""Tool interception for forked runs (constitution III — NON-NEGOTIABLE).

Resolution order, exact:
  1. Match a cached result by (run_id, seq) positionally.
  2. Fallback match by sha256(name + canonical_json(args)).
  3. No match -> typed mock {"result": {"mocked": true}, "error": null}.

A forked run NEVER executes a real tool. This module exposes NO code path to
real tool execution — it only resolves against previously recorded steps.

NOTE: Nestaro's tools are NOT LLM-native (single-shot fork emits no tool
calls), so this machinery is not exercised by the V1 demo path. It is
retained deliberately as the generality guarantee for tool-emitting agents
(V2/roadmap) — do not delete it as unused.
"""

import hashlib
import json
from typing import Any

from app.models import Step, StepType

TYPED_MOCK: dict[str, Any] = {"result": {"mocked": True}, "error": None}


def canonical_json(args: dict[str, Any]) -> str:
    """Deterministic serialization for hashing (research R3)."""
    return json.dumps(args, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def tool_call_hash(name: str, args: dict[str, Any]) -> str:
    """sha256(name + canonical_json(args)) — the fallback-match digest (research R3)."""
    payload = (name + canonical_json(args)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def resolve_tool_call(
    *, run_id: str, seq: int, name: str, args: dict[str, Any], recorded_steps: list[Step]
) -> dict[str, Any]:
    """Resolve a tool call a replayed model emits against the parent's recorded tool_call steps.

    Never executes a real tool — resolves only against `recorded_steps` (the
    parent run's own tool_call steps), by (run_id, seq) then by content hash,
    else returns the typed mock.
    """
    tool_steps = [s for s in recorded_steps if s.type == StepType.tool_call]

    # Tier 1: positional match by (run_id, seq).
    for step in tool_steps:
        if str(step.run_id) == str(run_id) and step.seq == seq:
            return step.output

    # Tier 2: fallback match by sha256(name + canonical_json(args)).
    target_hash = tool_call_hash(name, args)
    for step in tool_steps:
        recorded_name = step.input.get("name")
        recorded_args = step.input.get("args", {})
        if recorded_name is None:
            continue
        if tool_call_hash(recorded_name, recorded_args) == target_hash:
            return step.output

    # Tier 3: no match -> typed mock. No real tool is ever executed.
    return dict(TYPED_MOCK)
