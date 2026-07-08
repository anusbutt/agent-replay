"""Serialize a recorded run's steps into a compact transcript for judge prompts."""

from app.models import Step


def serialize_run(steps: list[Step]) -> str:
    """Render steps (ordered by seq) into a compact, human-readable transcript.

    Includes the system prompt, messages, tool calls with args/results, and
    state changes — enough context for an LLM judge without re-sending full
    verbatim JSON payloads.
    """
    lines: list[str] = []
    for step in steps:
        if step.type.value == "llm_call":
            messages = step.input.get("messages", [])
            for msg in messages:
                role = msg.get("role", "?")
                content = msg.get("content", "")
                lines.append(f"[step {step.seq}] {role}: {content}")
            choices = step.output.get("choices", [])
            if choices:
                reply = choices[0].get("message", {}).get("content", "")
                lines.append(f"[step {step.seq}] assistant (reply): {reply}")
        elif step.type.value == "tool_call":
            name = step.input.get("name", "?")
            args = step.input.get("args", {})
            result = step.output.get("result")
            error = step.output.get("error")
            lines.append(f"[step {step.seq}] tool_call {name}(args={args}) -> result={result} error={error}")
        elif step.type.value == "state_change":
            from_state = step.input.get("from_state", "?")
            to_state = step.input.get("to_state", "?")
            trigger = step.input.get("trigger", "?")
            lines.append(f"[step {step.seq}] state_change {from_state} -> {to_state} (trigger={trigger})")
    return "\n".join(lines)
