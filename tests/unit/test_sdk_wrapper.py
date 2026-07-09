"""Unit tests for replay.wrap() (FR-002, FR-006, FR-027).

Verifies verbatim recording of llm_call input/output, latency/tokens
population, and — critically — that the Authorization header never appears
in a recorded llm_call.input at any level, even if the host code passes it.
No real network call: wrap() only needs to buffer, not flush.
"""

import agentreplay as replay


class _FakeMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def model_dump(self):
        return {"role": self.role, "content": self.content}


class _FakeChoice:
    def __init__(self, message: _FakeMessage, finish_reason: str):
        self.message = message
        self.finish_reason = finish_reason

    def model_dump(self):
        return {"message": self.message.model_dump(), "finish_reason": self.finish_reason}


class _FakeUsage:
    def __init__(self, prompt_tokens: int, completion_tokens: int):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

    def model_dump(self):
        return {"prompt_tokens": self.prompt_tokens, "completion_tokens": self.completion_tokens}


class _FakeChatCompletion:
    """Mimics openai-python v1's pydantic ChatCompletion (has .model_dump())."""

    def __init__(self, id_: str, content: str, prompt_tokens: int, completion_tokens: int):
        self.id = id_
        self.choices = [_FakeChoice(_FakeMessage("assistant", content), "stop")]
        self.usage = _FakeUsage(prompt_tokens, completion_tokens)

    def model_dump(self):
        return {
            "id": self.id,
            "choices": [c.model_dump() for c in self.choices],
            "usage": self.usage.model_dump(),
        }


class _FakeCompletions:
    def __init__(self, response: _FakeChatCompletion):
        self._response = response
        self.last_kwargs: dict | None = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class _FakeChat:
    def __init__(self, completions: _FakeCompletions):
        self.completions = completions


class _FakeClient:
    def __init__(self, response: _FakeChatCompletion):
        self.chat = _FakeChat(_FakeCompletions(response))


def _init_sdk():
    replay.init(base_url="http://unused.invalid", api_key="test-key", agent_id="nestaro-test")


def test_wrapped_client_records_verbatim_request_and_response():
    _init_sdk()
    response = _FakeChatCompletion("gen-1", "Booking Saturday.", 512, 87)
    fake_client = _FakeClient(response)
    wrapped = replay.wrap(fake_client)

    messages = [
        {"role": "system", "content": "You are Nestaro."},
        {"role": "user", "content": "Previous conversation:\ncustomer: hi\nagent: hello"},
        {"role": "user", "content": "I need duct cleaning Friday"},
    ]
    result = wrapped.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
        extra_headers={"HTTP-Referer": "https://nestaro.com", "X-Title": "Nestaro"},
    )

    assert result is response  # wrapping never alters the call's return value

    batch = replay._state.buffer.drain()  # noqa: SLF001 — test-only introspection
    assert len(batch["steps"]) == 1
    step = batch["steps"][0]
    assert step["type"] == "llm_call"

    recorded_input = step["input"]
    assert recorded_input["model"] == "deepseek/deepseek-chat"
    assert recorded_input["messages"] == messages  # exact order preserved, incl. history message
    assert recorded_input["max_tokens"] == 1024
    assert recorded_input["temperature"] == 0.7
    assert recorded_input["headers"] == {"HTTP-Referer": "https://nestaro.com", "X-Title": "Nestaro"}

    recorded_output = step["output"]
    assert recorded_output["id"] == "gen-1"
    assert recorded_output["choices"][0]["message"]["content"] == "Booking Saturday."
    assert recorded_output["choices"][0]["finish_reason"] == "stop"
    assert recorded_output["usage"]["prompt_tokens"] == 512
    assert recorded_output["usage"]["completion_tokens"] == 87

    assert step["tokens_in"] == 512
    assert step["tokens_out"] == 87
    assert isinstance(step["latency_ms"], int)
    assert step["latency_ms"] >= 0


def test_recorded_llm_call_input_never_contains_authorization_key():
    _init_sdk()
    response = _FakeChatCompletion("gen-2", "reply", 10, 5)
    fake_client = _FakeClient(response)
    wrapped = replay.wrap(fake_client)

    wrapped.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[{"role": "user", "content": "hi"}],
        extra_headers={
            "Authorization": "Bearer sk-should-never-be-recorded",
            "authorization": "Bearer also-should-not-appear",
            "HTTP-Referer": "https://nestaro.com",
        },
    )

    batch = replay._state.buffer.drain()  # noqa: SLF001
    recorded_input = batch["steps"][0]["input"]

    def _assert_no_authorization_key(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                assert key.lower() != "authorization", f"Authorization key found: {obj}"
                _assert_no_authorization_key(value)
        elif isinstance(obj, list):
            for item in obj:
                _assert_no_authorization_key(item)

    _assert_no_authorization_key(recorded_input)
    # HTTP-Referer must still survive redaction — only auth is stripped
    assert recorded_input["headers"]["HTTP-Referer"] == "https://nestaro.com"
