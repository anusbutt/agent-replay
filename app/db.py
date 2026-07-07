"""Engine/session from DATABASE_URL; schema bootstrap via create_all (research R7)."""

import os
from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

# Env-var-only config (constitution VII). The fallback is the local compose dev DB
# so host-side dev/test works out of the box; it carries no secrets.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://agentreplay:agentreplay@localhost:5432/agentreplay",
)

engine = create_engine(DATABASE_URL)


def init_db() -> None:
    """Idempotent schema bootstrap — no migration tool in V1 (research R7)."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
