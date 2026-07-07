import os

# Defaults for host-side runs; in-container runs already set both (compose env wins).
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://agentreplay:agentreplay@localhost:5432/agentreplay",
)
os.environ.setdefault("AGENTREPLAY_API_KEY", "test-key")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers():
    return {"Authorization": f"Bearer {os.environ['AGENTREPLAY_API_KEY']}"}
