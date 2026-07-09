"""In-memory event buffer: seq assignment + IngestBatch shaping (FR-003, FR-004).

Pure logic, no network — transport.py owns the actual delivery.
"""

from datetime import UTC, datetime
from typing import Any


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class Buffer:
    def __init__(
        self,
        *,
        run_id: str,
        agent_id: str,
        session_id: str,
        run_metadata: dict[str, Any],
        started_at: str,
    ) -> None:
        self.run_id = run_id
        self.agent_id = agent_id
        self.session_id = session_id
        self.run_metadata = run_metadata
        self.started_at = started_at
        self.status = "running"
        self.ended_at: str | None = None
        self._next_seq = 1
        self._pending: list[dict[str, Any]] = []

    def add_step(
        self,
        type_: str,
        input_: dict[str, Any],
        output: dict[str, Any],
        *,
        latency_ms: int | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
    ) -> int:
        """Buffer one step, assigning the next contiguous 1-based seq. Returns that seq."""
        seq = self._next_seq
        self._next_seq += 1
        self._pending.append(
            {
                "seq": seq,
                "type": type_,
                "input": input_,
                "output": output,
                "latency_ms": latency_ms,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "created_at": _now_iso(),
            }
        )
        return seq

    def pending_count(self) -> int:
        return len(self._pending)

    def finalize(self, *, status: str, ended_at: str) -> None:
        self.status = status
        self.ended_at = ended_at

    def build_batch(self) -> dict[str, Any]:
        return {
            "run": {
                "id": self.run_id,
                "agent_id": self.agent_id,
                "session_id": self.session_id,
                "status": self.status,
                "run_metadata": self.run_metadata,
                "started_at": self.started_at,
                "ended_at": self.ended_at,
            },
            "steps": self._pending,
        }

    def drain(self) -> dict[str, Any]:
        """Return the current batch (run header + pending steps) and clear pending steps.

        The seq counter is NOT reset — subsequent events continue numbering
        from where they left off, since seq is per-run, not per-batch.
        """
        batch = self.build_batch()
        self._pending = []
        return batch
