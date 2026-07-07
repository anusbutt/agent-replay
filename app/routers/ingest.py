"""POST /ingest — batched run upsert + insert-only steps (FR-007, FR-008, research R2).

Idempotency contract:
- Run header is upserted; steps are insert-only under UNIQUE (run_id, seq).
- Duplicate/invalid steps are rejected PER-ITEM; valid items persist.
- Upsert protections (constitution VI): never downgrade a `flagged` status;
  the run_metadata merge never removes or overwrites `detection`/`analysis`.
"""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Run, RunStatus, Step, StepType
from app.schemas import IngestBatch, IngestResult, RejectedStep

router = APIRouter()

_VALID_STEP_TYPES = {t.value for t in StepType}
_PROTECTED_METADATA_KEYS = ("detection", "analysis")


@router.post("/ingest", response_model=IngestResult)
def ingest_batch(batch: IngestBatch, session: Session = Depends(get_session)) -> IngestResult:
    run = session.get(Run, batch.run.id)
    if run is None:
        run = Run(
            id=batch.run.id,
            agent_id=batch.run.agent_id,
            session_id=batch.run.session_id,
            status=batch.run.status,
            run_metadata=batch.run.run_metadata or {},
            started_at=batch.run.started_at,
            ended_at=batch.run.ended_at,
        )
        session.add(run)
    else:
        # Never downgrade a flagged run (a late SDK batch must not clear a flag).
        if run.status != RunStatus.flagged:
            run.status = batch.run.status
        if batch.run.ended_at is not None:
            run.ended_at = batch.run.ended_at
        # Merge, not replace — and never clobber verdict keys (constitution VI).
        existing_md = run.run_metadata or {}
        merged = {**existing_md, **(batch.run.run_metadata or {})}
        for key in _PROTECTED_METADATA_KEYS:
            if key in existing_md:
                merged[key] = existing_md[key]
        run.run_metadata = merged

    existing_seqs = set(
        session.exec(select(Step.seq).where(Step.run_id == batch.run.id)).all()
    )

    accepted = 0
    rejected: list[RejectedStep] = []
    for item in batch.steps:
        if item.seq < 1:
            rejected.append(RejectedStep(seq=item.seq, error="seq must be a 1-based integer"))
        elif item.type not in _VALID_STEP_TYPES:
            rejected.append(
                RejectedStep(seq=item.seq, error=f"invalid step type '{item.type}'")
            )
        elif item.seq in existing_seqs:
            rejected.append(RejectedStep(seq=item.seq, error="duplicate (run_id, seq)"))
        else:
            session.add(
                Step(
                    run_id=batch.run.id,
                    seq=item.seq,
                    type=StepType(item.type),
                    input=item.input,
                    output=item.output,
                    latency_ms=item.latency_ms,
                    tokens_in=item.tokens_in,
                    tokens_out=item.tokens_out,
                    created_at=item.created_at,
                )
            )
            existing_seqs.add(item.seq)
            accepted += 1

    session.commit()
    return IngestResult(run_id=batch.run.id, accepted=accepted, rejected=rejected)
