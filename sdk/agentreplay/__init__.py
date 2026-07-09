"""AgentReplay SDK — records every step of a host agent's execution invisibly.

Public API: init, wrap, tool, record_state_change, flush, end_run.
The SDK must never raise into host agent code (constitution V, pinned
decision 5) — every transport/recording error is swallowed and logged
locally only.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from agentreplay.buffer import Buffer
from agentreplay.state import record_state_change
from agentreplay.tool import tool
from agentreplay.transport import send_batch
from agentreplay.wrapper import wrap

__all__ = ["init", "wrap", "tool", "record_state_change", "flush", "end_run"]

_logger = logging.getLogger("agentreplay")

# Auto-flush once this many steps are buffered, so long conversations don't
# hold everything in memory until end_run(). Explicit flush()/end_run()
# always drains regardless of this threshold.
AUTO_FLUSH_THRESHOLD = 10


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class _SDKState:
    def __init__(self, *, base_url: str, api_key: str, agent_id: str, session_id: str, run_metadata: dict[str, Any]):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.agent_id = agent_id
        self.session_id = session_id
        self.buffer = Buffer(
            run_id=str(uuid.uuid4()),
            agent_id=agent_id,
            session_id=session_id,
            run_metadata=run_metadata or {},
            started_at=_now_iso(),
        )


_state: _SDKState | None = None


def init(
    base_url: str,
    api_key: str,
    agent_id: str,
    session_id: str | None = None,
    run_metadata: dict[str, Any] | None = None,
) -> None:
    """Start a new recorded run. Call once per host agent conversation."""
    global _state
    _state = _SDKState(
        base_url=base_url,
        api_key=api_key,
        agent_id=agent_id,
        session_id=session_id or str(uuid.uuid4()),
        run_metadata=run_metadata or {},
    )


def flush() -> None:
    """Deliver any buffered steps to the ingest API now. Never raises."""
    if _state is None:
        return
    try:
        batch = _state.buffer.drain()
        if batch["steps"] or _state.buffer.status != "running":
            send_batch(_state.base_url, _state.api_key, batch)
    except Exception as exc:  # noqa: BLE001 — flush must never raise into host code
        _logger.warning("agentreplay: flush failed: %s", exc)


def end_run(status: str = "completed") -> None:
    """Finalize the current run (status + ended_at) and flush. Never raises."""
    if _state is None:
        return
    try:
        _state.buffer.finalize(status=status, ended_at=_now_iso())
    except Exception as exc:  # noqa: BLE001
        _logger.warning("agentreplay: finalize failed: %s", exc)
    flush()
