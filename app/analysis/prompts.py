"""Strict-JSON prompt templates + defensive extraction for the LLM-judge (research R5)."""

import json
import re
from typing import Any

DETECTION_SYSTEM_PROMPT = """You are a strict QA judge reviewing a recorded AI agent conversation transcript. \
Determine whether the agent's action contradicts the user's expressed intent (e.g. the customer \
asked for one day and the agent booked a different day).

Respond with ONLY a single JSON object, no other text, in exactly this shape:
{"verdict": "pass" or "fail", "reason": "<short explanation>", \
"contradiction": {"user_intent": "<...>", "agent_action": "<...>"} or null}

Use "fail" only when there is a clear contradiction between what the user asked for and what the \
agent did. Use "pass" when the agent's action matches the user's request."""

ANALYSIS_SYSTEM_PROMPT = """You are a root-cause analyst reviewing a recorded AI agent conversation \
transcript that has already been flagged as failing. Identify the step (by its [step N] number) \
where the agent's behavior diverged from the user's intent, explain the root cause, and suggest a \
concrete fix to the agent's system prompt.

Respond with ONLY a single JSON object, no other text, in exactly this shape:
{"failing_step": <integer step number>, "root_cause": "<short explanation>", \
"suggested_fix": "<concrete system-prompt addition or edit>"}"""


def build_detection_messages(transcript: str) -> list[dict]:
    return [
        {"role": "system", "content": DETECTION_SYSTEM_PROMPT},
        {"role": "user", "content": transcript},
    ]


def build_analysis_messages(transcript: str) -> list[dict]:
    return [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": transcript},
    ]


def extract_json_object(text: str) -> dict[str, Any]:
    """Defensively extract the first top-level JSON object from model output.

    Raises ValueError if no valid JSON object can be found — callers must
    treat this as a parse failure and write nothing (research R5 edge case).
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object found in model output: {text!r}")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in model output: {exc}") from exc
