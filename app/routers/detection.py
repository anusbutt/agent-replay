"""POST /detect/sweep — evaluate recorded runs for semantic contradiction (FR-021, FR-022)."""

import uuid

from fastapi import APIRouter, Body, Depends
from sqlmodel import Session, select

from app.analysis.client import chat_completion
from app.analysis.prompts import build_detection_messages, extract_json_object
from app.analysis.serializer import serialize_run
from app.db import get_session
from app.models import Run, RunStatus, Step
from app.schemas import Contradiction, DetectionVerdict, SweepResult

router = APIRouter()


def _candidate_runs(session: Session, run_ids: list[uuid.UUID] | None) -> list[Run]:
    if run_ids:
        return [r for r in (session.get(Run, rid) for rid in run_ids) if r is not None]
    query = select(Run).where(Run.status != RunStatus.running, Run.parent_run_id.is_(None))
    return list(session.exec(query).all())


@router.post("/detect/sweep", response_model=list[SweepResult])
def detect_sweep(
    body: dict | None = Body(default=None),
    session: Session = Depends(get_session),
) -> list[SweepResult]:
    run_ids_raw = (body or {}).get("run_ids")
    run_ids = [uuid.UUID(str(r)) for r in run_ids_raw] if run_ids_raw else None

    results: list[SweepResult] = []
    for run in _candidate_runs(session, run_ids):
        steps = session.exec(select(Step).where(Step.run_id == run.id).order_by(Step.seq)).all()
        transcript = serialize_run(steps)

        try:
            raw = chat_completion(build_detection_messages(transcript))
            parsed = extract_json_object(raw)
            verdict = DetectionVerdict.model_validate(parsed)
        except Exception as exc:  # defensive: judge/network/parse failures per research R5
            results.append(
                SweepResult(
                    run_id=run.id,
                    detection=None,
                    status_after=run.status,
                    error=f"detection judge failed: {exc}",
                )
            )
            continue

        run.run_metadata = {**run.run_metadata, "detection": verdict.model_dump()}
        if verdict.verdict == "fail":
            run.status = RunStatus.flagged
        session.add(run)
        session.commit()

        results.append(
            SweepResult(run_id=run.id, detection=verdict, status_after=run.status)
        )

    return results
