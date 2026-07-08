"""Pydantic request/response bodies per contracts/api.openapi.yaml."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models import RunStatus


class RunIn(BaseModel):
    """Run header fields carried by an ingest batch (research R2)."""

    id: uuid.UUID
    agent_id: str
    session_id: str
    status: RunStatus
    run_metadata: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    ended_at: datetime | None = None


class StepIn(BaseModel):
    """One recorded step in an ingest batch.

    `seq` and `type` are deliberately lenient here: invalid values are rejected
    PER-ITEM by the ingest handler (research R2), not by whole-batch validation.
    """

    seq: int
    type: str
    input: dict[str, Any]
    output: dict[str, Any]
    latency_ms: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    created_at: datetime | None = None


class IngestBatch(BaseModel):
    run: RunIn
    steps: list[StepIn]


class RejectedStep(BaseModel):
    seq: int
    error: str


class IngestResult(BaseModel):
    run_id: uuid.UUID
    accepted: int
    rejected: list[RejectedStep]


class StepOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    seq: int
    type: str
    input: dict[str, Any]
    output: dict[str, Any]
    latency_ms: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    created_at: datetime | None = None


class RunOut(BaseModel):
    id: uuid.UUID
    agent_id: str
    session_id: str
    status: RunStatus
    parent_run_id: uuid.UUID | None = None
    fork_step: int | None = None
    run_metadata: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    ended_at: datetime | None = None


class RunDetail(RunOut):
    steps: list[StepOut]  # ordered by seq ascending


class ForkRequest(BaseModel):
    fork_step: int = Field(ge=1)
    modification: dict[str, Any]  # e.g. {"system_prompt": "..."}
    temperature: float | None = None  # None -> temperature 0 (constitution IV)


class AnalysisVerdict(BaseModel):
    failing_step: int
    root_cause: str
    suggested_fix: str


class Contradiction(BaseModel):
    user_intent: str
    agent_action: str


class DetectionVerdict(BaseModel):
    verdict: Literal["pass", "fail"]
    reason: str
    contradiction: Contradiction | None = None


class SweepResult(BaseModel):
    run_id: uuid.UUID
    detection: DetectionVerdict | None = None
    status_after: RunStatus
    error: str | None = None  # set on judge/parse failure; detection is None and nothing was stored


class Error(BaseModel):
    detail: str
