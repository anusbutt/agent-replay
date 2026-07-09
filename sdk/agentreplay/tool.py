"""@replay.tool — records a real Python tool function's call as a tool_call step.

Per docs/DATA_CONTRACT.md: in Nestaro, tools are real Python functions (not
LLM-native function calls), invoked after the text response is parsed. The
decorated function's own behavior (return value, exceptions) is never
altered — only AgentReplay's OWN recording code is error-swallowed
(constitution V).
"""

import functools
import inspect
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def _bind_args(func: Callable[..., Any], args: tuple, kwargs: dict) -> dict[str, Any]:
    try:
        bound = inspect.signature(func).bind(*args, **kwargs)
        bound.apply_defaults()
        return dict(bound.arguments)
    except TypeError:
        # Fall back to raw kwargs if binding fails for any reason — recording
        # must never raise, and a best-effort snapshot beats none.
        return dict(kwargs)


def tool(func: F) -> F:
    @functools.wraps(func)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        result: Any = None
        error: str | None = None
        raised: BaseException | None = None
        try:
            result = func(*args, **kwargs)
        except Exception as exc:  # the tool's OWN exception — real, must propagate
            error = str(exc)
            raised = exc

        try:
            import agentreplay

            state = agentreplay._state
            if state is not None:
                bound_args = _bind_args(func, args, kwargs)
                state.buffer.add_step(
                    "tool_call",
                    {"name": func.__name__, "args": bound_args},
                    {"result": result, "error": error},
                )
                if state.buffer.pending_count() >= agentreplay.AUTO_FLUSH_THRESHOLD:
                    agentreplay.flush()
        except Exception as record_exc:  # noqa: BLE001 — recording must never raise into host code
            try:
                import agentreplay

                agentreplay._logger.warning("agentreplay: failed to record tool_call: %s", record_exc)
            except Exception:  # noqa: BLE001 — even logging failures must not escape
                pass

        if raised is not None:
            raise raised
        return result

    return wrapped  # type: ignore[return-value]
