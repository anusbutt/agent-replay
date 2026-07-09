"""OpenAI-compatible chat client for the analysis/detection judge (research R5).

Reads ANALYSIS_BASE_URL / ANALYSIS_API_KEY. Switching to the Fireworks
fallback is an env-var swap only — no code change (constitution: fixed stack).
"""

import os

import httpx


class AnalysisClientError(Exception):
    """Raised when the analysis endpoint is unavailable or errors."""


def chat_completion(messages: list[dict], *, model: str = "google/gemma-4-31b-it") -> str:
    """POST /chat/completions to ANALYSIS_BASE_URL; returns the assistant content string."""
    base_url = os.environ["ANALYSIS_BASE_URL"]
    api_key = os.environ.get("ANALYSIS_API_KEY", "")

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
