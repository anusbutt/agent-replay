"""POST /runs/{run_id}/fork — fork a run from a step with a modification (FR-014..018)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Run, Step
from app.replay.engine import ForkExecutionError, ForkValidationError, execute_fork
from app.schemas import ForkRequest, RunDetail, StepOut

router = APIRouter()


@router.post("/runs/{run_id}/fork", response_model=RunDetail, status_code=201)
def fork_run(
    run_id: uuid.UUID, body: ForkRequest, session: Session = Depends(get_session)
) -> RunDetail:
    parent = session.get(Run, run_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="run not found")

    try:
        fork = execute_fork(
            session,
            parent=parent,
            fork_step=body.fork_step,
            modification=body.modification,
            temperature=body.temperature,
        )
    except ForkValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ForkExecutionError as exc:
        raise HTTPException(status_code=502, detail=f"fork replay call failed: {exc}") from exc

    steps = session.exec(select(Step).where(Step.run_id == fork.id).order_by(Step.seq)).all()
    return RunDetail(
        id=fork.id,
        agent_id=fork.agent_id,
        session_id=fork.session_id,
        status=fork.status,
        parent_run_id=fork.parent_run_id,
        fork_step=fork.fork_step,
        run_metadata=fork.run_metadata,
        started_at=fork.started_at,
        ended_at=fork.ended_at,
        steps=[StepOut.model_validate(s, from_attributes=True) for s in steps],
    )
