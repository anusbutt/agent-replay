from fastapi import FastAPI

app = FastAPI(title="AgentReplay API", version="1.0.0")


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}
