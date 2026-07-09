import os


def _test_database_url() -> str:
    """Force pytest onto a SEPARATE database from whatever the app/demo uses.

    docs/DATA_CONTRACT.md doesn't require this, but sharing one Postgres
    between tests and the seeded demo data caused repeated real pollution
    incidents this session (see PROGRESS.md) — test runs kept leaving dozens
    of junk rows in the same db the T031/T039 demo evidence lives in, and in
    US3's sweep-selectivity test that pollution became an actual assertion
    failure (candidate-run count included leftovers from prior pytest
    invocations), not just cosmetic clutter.
    """
    base = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://agentreplay:agentreplay@localhost:5432/agentreplay",
    )
    prefix, _, dbname = base.rpartition("/")
    return base if dbname.endswith("_test") else f"{prefix}/{dbname}_test"


os.environ["DATABASE_URL"] = _test_database_url()
os.environ.setdefault("AGENTREPLAY_API_KEY", "test-key")


def _ensure_test_database_exists(url: str) -> None:
    import psycopg

    sqla_url = url.replace("postgresql+psycopg://", "postgresql://", 1)
    prefix, _, dbname = sqla_url.rpartition("/")
    try:
        with psycopg.connect(f"{prefix}/postgres", autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
                if cur.fetchone() is None:
                    cur.execute(f'CREATE DATABASE "{dbname}"')
    except Exception:
        pass  # best-effort; a real connectivity problem surfaces via create_all() below


_ensure_test_database_exists(os.environ["DATABASE_URL"])

import psycopg  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402, F401 — registers Run/Step with SQLModel.metadata before create_all
from app.db import init_db  # noqa: E402

init_db()  # idempotent create_all — guarantees tables exist before the truncate below


def _truncate_test_tables() -> None:
    sqla_url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(sqla_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE steps, runs RESTART IDENTITY CASCADE")


@pytest.fixture(scope="session", autouse=True)
def _clean_test_database():
    """Start every pytest session from an empty, isolated database."""
    _truncate_test_tables()
    yield


@pytest.fixture()
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers():
    return {"Authorization": f"Bearer {os.environ['AGENTREPLAY_API_KEY']}"}
