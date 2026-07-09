"""replay.wrap(client) — records llm_call verbatim (FR-002, FR-006, FR-027).

Intercepts an OpenAI-compatible client's chat.completions.create, recording
the exact request and response. The underlying call's own behavior (return
value, exceptions) is never altered — only AgentReplay's OWN recording code
is wrapped in error-swallowing, per constitution V (the SDK never raises
into host code from its OWN failures; a genuine LLM-call error is the host's
to see, not ours to hide).
"""

import time
from typing import Any


def _redact_authorization(obj: Any) -> Any:
    """Recursively strip any 'authorization' key (case-insensitive) at any level.

    FR-027: a recorded llm_call.input MUST NOT contain an Authorization key
    at any level — redaction happens at the SDK boundary before buffering.
    """
    if isinstance(obj, dict):
        return {
            key: _redact_authorization(value)
            for key, value in obj.items()
            if key.lower() != "authorization"
        }
    if isinstance(obj, list):
        return [_redact_authorization(item) for item in obj]
    return obj


def _serialize_response(response: Any) -> dict[str, Any]:
    """Best-effort JSON-safe serialization without depending on any specific
    OpenAI client library (SDK's only runtime dependency is httpx)."""
    if isinstance(response, dict):
        return response
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if hasattr(response, "to_dict"):
        return response.to_dict()
    return dict(vars(response))


def _build_request_snapshot(kwargs: dict[str, Any]) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for key in ("model", "messages", "max_tokens", "temperature"):
        if key in kwargs:
            snapshot[key] = kwargs[key]
    headers = kwargs.get("extra_headers") or kwargs.get("headers")
    if headers:
        snapshot["headers"] = headers
    return _redact_authorization(snapshot)


def wrap(client: Any) -> Any:
    """Wrap an OpenAI-compatible client so chat.completions.create is recorded.

    Mutates and returns the same client object (matches quickstart.md usage:
    `client = replay.wrap(openai_client)`).
    """
    import agentreplay  # local import: avoids a circular import at module load time

    original_create = client.chat.completions.create

    def wrapped_create(*args: Any, **kwargs: Any) -> Any:
        start = time.monotonic()
        response = original_create(*args, **kwargs)  # the real call — never touched by our error handling
        latency_ms = int((time.monotonic() - start) * 1000)

        try:
            state = agentreplay._state
            if state is None:
                return response  # no active run (host never called init()) — stay invisible

            request_snapshot = _build_request_snapshot(kwargs)
            response_snapshot = _serialize_response(response)
            usage = response_snapshot.get("usage", {}) or {}

            state.buffer.add_step(
                "llm_call",
                request_snapshot,
                response_snapshot,
                latency_ms=latency_ms,
                tokens_in=usage.get("prompt_tokens"),
                tokens_out=usage.get("completion_tokens"),
            )
            if state.buffer.pending_count() >= agentreplay.AUTO_FLUSH_THRESHOLD:
                agentreplay.flush()
        except Exception as exc:  # noqa: BLE001 — recording must never raise into host code
            agentreplay._logger.warning("agentreplay: failed to record llm_call: %s", exc)

        return response

    client.chat.completions.create = wrapped_create
    return client
