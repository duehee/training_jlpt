"""FakeProvider + Protocol 적합성 단위 테스트 (DB/실 API 불필요)."""

import asyncio

from src.services.llm.base import ChatMessage, LlmProvider
from src.services.llm.fake import FakeProvider


def test_fake_provider_satisfies_protocol() -> None:
    assert isinstance(FakeProvider(), LlmProvider)


def test_fake_provider_default_response() -> None:
    provider = FakeProvider(default="HELLO")
    result = asyncio.run(
        provider.chat(
            [ChatMessage(role="user", content="anything")], model="gpt-4o-mini"
        )
    )
    assert result.text == "HELLO"
    assert result.model == "gpt-4o-mini"


def test_fake_provider_keyed_response_and_call_record() -> None:
    provider = FakeProvider(responses={"q1": "a1"})
    r = asyncio.run(
        provider.chat([ChatMessage(role="user", content="q1")], model="m")
    )
    assert r.text == "a1"
    assert provider.call_count == 1
    assert provider.calls[0]["model"] == "m"
