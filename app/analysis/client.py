"""OpenAI-compatible chat client for the analysis/detection judge (research R5).

Reads ANALYSIS_BASE_URL / ANALYSIS_API_KEY. Switching to the Fireworks
fallback is an env-var swap only — no code change (constitution: fixed stack).
"""

import os
from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.analysis.prompts import extract_json_object

T = TypeVar("T", bound=BaseModel)


class AnalysisClientError(Exception):
    """Raised when the analysis endpoint is unavailable or errors."""


def query_judge(messages: list[dict], verdict_cls: type[T], *, max_attempts: int = 2) -> T:
    """Call the judge model, extract+validate strict JSON, retrying once on
    parse/validation failure before giving up.

    LLM structured-output calls occasionally produce malformed JSON (a
    missing/null required field) even at temperature 0 — a single retry
    absorbs that flakiness without weakening the "never write garbage"
    guarantee: after max_attempts, the last error still propagates and the
    caller stores nothing (research R5 edge case).
    """
    last_exc: Exception | None = None
    for _ in range(max_attempts):
        try:
            raw = chat_completion(messages)
            parsed = extract_json_object(raw)
            return verdict_cls.model_validate(parsed)
        except Exception as exc:  # noqa: BLE001 — retry on any parse/validation/client failure
            last_exc = exc
            continue
    assert last_exc is not None
    raise last_exc


def chat_completion(messages: list[dict], *, model: str | None = None) -> str:
    """POST /chat/completions to ANALYSIS_BASE_URL; returns the assistant content string.

    Model id is provider-specific (OpenRouter: google/gemma-4-31b-it;
    Fireworks: accounts/fireworks/models/...), so ANALYSIS_MODEL rides along
    with ANALYSIS_BASE_URL/ANALYSIS_API_KEY as the provider-swap trio.
    """
    if model is None:
        model = os.environ.get("ANALYSIS_MODEL", "google/gemma-4-31b-it").strip()
    # .strip() guards against trailing newlines pasted into hosted env-var
    # editors — a stray \n makes the Authorization header illegal.
    base_url = os.environ["ANALYSIS_BASE_URL"].strip().rstrip("/")
    api_key = os.environ.get("ANALYSIS_API_KEY", "").strip()

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = httpx.post(
            f"{base_url}/chat/completions",
            json={"model": model, "messages": messages, "temperature": 0},
            headers=headers,
            timeout=60,
        )
    except httpx.HTTPError as exc:
        raise AnalysisClientError(f"analysis endpoint unreachable: {exc}") from exc

    if resp.status_code >= 400:
        raise AnalysisClientError(f"analysis endpoint returned {resp.status_code}: {resp.text}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise AnalysisClientError(f"unexpected analysis response shape: {data}") from exc
