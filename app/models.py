"""SQLModel entities mirroring docs/DATA_CONTRACT.md 1:1 (Data Contract Supremacy).

Do not add, rename, or drop fields without updating docs/DATA_CONTRACT.md first.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import Column, DateTime, UniqueConstraint, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class RunStatus(str, Enum):
    running = "running"
    completed = "completed"
    failed = "failed"
    flagged = "flagged"


class StepType(str, Enum):
    llm_call = "llm_call"
    tool_call = "tool_call"
    state_change = "state_change"


class Run(SQLModel, table=True):
    __tablename__ = "runs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_id: str = Field(index=True)
    session_id: str = Field(index=True)
    status: RunStatus = Field(
        sa_column=Column(
            SAEnum(RunStatus, name="run_status", values_callable=lambda e: [m.value for m in e]),
            nullable=False,
        )
    )
    parent_run_id: uuid.UUID | None = Field(default=None, foreign_key="runs.id", nullable=True)
    fork_step: int | None = Field(default=None, nullable=True)
    run_metadata: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )
    started_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    ended_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class Step(SQLModel, table=True):
    __tablename__ = "steps"
    __table_args__ = (UniqueConstraint("run_id", "seq", name="uq_steps_run_id_seq"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    run_id: uuid.UUID = Field(foreign_key="runs.id", index=True)
    seq: int  # 1-based per run; UNIQUE (run_id, seq)
    type: StepType = Field(
        sa_column=Column(
            SAEnum(StepType, name="step_type", values_callable=lambda e: [m.value for m in e]),
            nullable=False,
        )
    )
    input: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    output: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    latency_ms: int | None = Field(default=None, nullable=True)
    tokens_in: int | None = Field(default=None, nullable=True)  # llm_call only
    tokens_out: int | None = Field(default=None, nullable=True)  # llm_call only
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True, server_default=func.now()),
    )
