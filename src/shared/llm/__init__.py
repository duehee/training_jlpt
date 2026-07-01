"""LLM provider 패키지.

`get_provider()`로 런타임 provider를 얻는다 (settings 기반).
"""

from __future__ import annotations

from src.core.config import settings
from src.shared.llm.base import ChatMessage, ChatResult, LlmProvider
from src.shared.llm.fake import FakeProvider
from src.shared.llm.openai_provider import OpenAIProvider

__all__ = [
    "ChatMessage",
    "ChatResult",
    "LlmProvider",
    "OpenAIProvider",
    "FakeProvider",
    "get_provider",
]


def get_provider() -> LlmProvider:
    """settings 기반 런타임 provider. 키 미설정 시 명시적 에러."""
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY 미설정 — provider 생성 불가 (.env 확인)"
        )
    return OpenAIProvider(settings.openai_api_key)
