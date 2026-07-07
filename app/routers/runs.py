"""GET /runs and GET /runs/{run_id} — list + detail with steps ordered by seq."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models import Run, RunStatus, Step
from app.schemas import RunDetail, RunOut, StepOut

router = APIRouter()


@router.get("/runs", response_model=list[RunOut])
def list_runs(
    agent_id: str | None = None,
    session_id: str | None = None,
    status: RunStatus | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[RunOut]:
    query = select(Run)
    if agent_id is not None:
        query = query.where(Run.agent_id == agent_id)
    if session_id is not None:
        query = query.where(Run.session_id == session_id)
    if status is not None:
        query = query.where(Run.status == status)
    query = query.order_by(Run.started_at.desc().nullslast()).limit(limit).offset(offset)
    runs = session.exec(query).all()
    return [RunOut.model_validate(run, from_attributes=True) for run in runs]


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: uuid.UUID, session: Session = Depends(get_session)) -> RunDetail:
    run = session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    steps = session.exec(
        select(Step).where(Step.run_id == run_id).order_by(Step.seq)
    ).all()
    return RunDetail(
        **RunOut.model_validate(run, from_attributes=True).model_dump(),
        steps=[StepOut.model_validate(s, from_attributes=True) for s in steps],
    )
