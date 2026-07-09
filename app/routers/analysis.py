"""POST /runs/{run_id}/analyze — root-cause verdict for a flagged run (FR-019, FR-020)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.analysis.client import AnalysisClientError, query_judge
from app.analysis.prompts import build_analysis_messages
from app.analysis.serializer import serialize_run
from app.db import get_session
from app.models import Run, Step
from app.schemas import AnalysisVerdict

router = APIRouter()


@router.post("/runs/{run_id}/analyze", response_model=AnalysisVerdict)
def analyze_run(run_id: uuid.UUID, session: Session = Depends(get_session)) -> AnalysisVerdict:
    run = session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    steps = session.exec(select(Step).where(Step.run_id == run_id).order_by(Step.seq)).all()
    transcript = serialize_run(steps)

    try:
        verdict = query_judge(build_analysis_messages(transcript), AnalysisVerdict)
    except AnalysisClientError as exc:
        raise HTTPException(status_code=502, detail=f"analysis model unavailable: {exc}") from exc
    except Exception as exc:  # defensive parse per research R5
        raise HTTPException(status_code=502, detail=f"analysis model returned unparseable output: {exc}") from exc

    run.run_metadata = {**run.run_metadata, "analysis": verdict.model_dump()}
    session.add(run)
    session.commit()

    return verdict
