import os
import secrets
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI, Header, HTTPException

from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Import models so create_all sees every table before bootstrap.
    import app.models  # noqa: F401

    init_db()
    yield


def require_api_key(authorization: str | None = Header(default=None)) -> None:
    """Single static API key — Authorization: Bearer $AGENTREPLAY_API_KEY.

    Nothing beyond one static key (scope guard, FR-009).
    """
    expected = os.environ.get("AGENTREPLAY_API_KEY", "")
    supplied = ""
    if authorization and authorization.startswith("Bearer "):
        supplied = authorization.removeprefix("Bearer ").strip()
    if not expected or not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="invalid or missing API key")


app = FastAPI(title="AgentReplay API", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


from app.routers import ingest, runs  # noqa: E402

app.include_router(ingest.router, dependencies=[Depends(require_api_key)])
app.include_router(runs.router, dependencies=[Depends(require_api_key)])
