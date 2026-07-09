# AgentReplay backend image (compose service: backend; Railway deploy artifact).
# Includes dev deps (pytest/respx) and tests/ so `docker compose exec backend pytest`
# works per quickstart.md. Config via environment variables only — no secrets baked in.
FROM python:3.11-slim

WORKDIR /srv/agentreplay

COPY pyproject.toml ./
COPY app ./app
COPY tests ./tests
COPY scripts ./scripts
COPY sdk ./sdk

RUN pip install --no-cache-dir -e ".[dev]"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
