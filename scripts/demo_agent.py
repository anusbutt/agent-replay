"""Minimal Nestaro-like agent, instrumented with the AgentReplay SDK.

Demonstrates live recording (US2): a short duct-cleaning conversation where
the customer asks for Friday, a real LLM call replies, a tool books an
appointment, and state changes mark the conversation's progress — all
recorded invisibly via the SDK, ending with end_run().

Uses a minimal hand-rolled OpenAI-compatible client (httpx only, no `openai`
package dependency — matches replay.wrap()'s duck-typed interface: any
object exposing chat.completions.create(**kwargs) -> object with
.model_dump()) pointed at REPLAY_BASE_URL/REPLAY_API_KEY (OpenRouter).

Usage: python scripts/demo_agent.py
Env: AGENTREPLAY_BASE_URL (default http://localhost:8000),
     AGENTREPLAY_API_KEY  (default dev-key — the compose default),
     REPLAY_BASE_URL/REPLAY_API_KEY (real OpenAI-compatible endpoint for the
     live LLM call — defaults to OpenRouter).
"""

import os
import time as _time
from types import SimpleNamespace

import httpx

import agentreplay as replay

AGENTREPLAY_BASE_URL = os.environ.get("AGENTREPLAY_BASE_URL", "http://localhost:8000")
AGENTREPLAY_API_KEY = os.environ.get("AGENTREPLAY_API_KEY", "dev-key")
LLM_BASE_URL = os.environ.get("REPLAY_BASE_URL", "https://openrouter.ai/api/v1")
LLM_API_KEY = os.environ.get("REPLAY_API_KEY", "")
LLM_MODEL = os.environ.get("DEMO_AGENT_MODEL", "deepseek/deepseek-chat")


class _Response:
    """Wraps a raw JSON dict so replay.wrap() can call .model_dump() on it,
    same duck-typed contract a real openai-python response satisfies."""

    def __init__(self, data: dict):
        self._data = data

    def model_dump(self) -> dict:
        return self._data


class SimpleOpenAICompatibleClient:
    """Minimal OpenAI-compatible client using only httpx — no `openai` package
    dependency, demonstrating replay.wrap() works with any duck-typed client."""

    def __init__(self, base_url: str, api_key: str):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def _create(self, **kwargs) -> _Response:
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        extra = kwargs.pop("extra_headers", None)
        if extra:
            headers.update(extra)
        resp = httpx.post(f"{self._base_url}/chat/completions", json=kwargs, headers=headers, timeout=30)
        resp.raise_for_status()
        return _Response(resp.json())


SYSTEM_PROMPT = (
    "You are Nestaro, the friendly lead-qualification assistant for Breeze Home "
    "Services, a duct-cleaning company. Always book the exact day the customer "
    "requested. Keep replies short and warm."
)


@replay.tool
def book_appointment(day: str, time: str, customer_id: str) -> dict:
    """A real Python function with a (simulated) side effect — Nestaro's tools
    are not LLM-native, per docs/DATA_CONTRACT.md."""
    return {"booking_id": f"bk_demo_{int(_time.time())}", "confirmed": True}


def main() -> int:
    replay.init(
        base_url=AGENTREPLAY_BASE_URL,
        api_key=AGENTREPLAY_API_KEY,
        agent_id="nestaro-demo",
        session_id=f"demo-{int(_time.time())}",
        run_metadata={"channel": "demo_agent_script"},
    )

    raw_client = SimpleOpenAICompatibleClient(LLM_BASE_URL, LLM_API_KEY)
    client = replay.wrap(raw_client)

    replay.record_state_change("GREETING", "QUOTING", "service_identified")

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "I need duct cleaning Friday"},
        ],
        max_tokens=200,
        temperature=0.7,
        extra_headers={"HTTP-Referer": "https://nestaro.com", "X-Title": "Nestaro Lead Qualifier"},
    )
    reply = response.model_dump()["choices"][0]["message"]["content"]
    print(f"agent: {reply}")

    replay.record_state_change("QUOTING", "BOOKING", "agent_selected_slot")

    booking = book_appointment(day="friday", time="10:00", customer_id="demo_customer")
    print(f"booked: {booking}")

    replay.end_run(status="completed")
    print(f"run recorded: agent_id=nestaro-demo — view it at {AGENTREPLAY_BASE_URL.replace('8000', '3000')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
