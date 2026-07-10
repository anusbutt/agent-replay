import os
import secrets
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
    expected = os.environ.get("AGENTREPLAY_API_KEY", "").strip()
    supplied = ""
    if authorization and authorization.startswith("Bearer "):
        supplied = authorization.removeprefix("Bearer ").strip()
    if not expected or not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="invalid or missing API key")


app = FastAPI(title="AgentReplay API", version="1.0.0", lifespan=lifespan)

# The dashboard calls this API directly from the browser (client components:
# detect sweep, analyze, fork buttons). Every route but /health already
# requires the static API key, so CORS here only controls which origins may
# READ responses — it is not an auth boundary, so a permissive origin policy
# does not weaken FR-009's scope guard (single static key, nothing more).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


from app.routers import analysis, detection, fork, ingest, runs  # noqa: E402

app.include_router(ingest.router, dependencies=[Depends(require_api_key)])
app.include_router(runs.router, dependencies=[Depends(require_api_key)])
app.include_router(fork.router, dependencies=[Depends(require_api_key)])
app.include_router(analysis.router, dependencies=[Depends(require_api_key)])
app.include_router(detection.router, dependencies=[Depends(require_api_key)])
