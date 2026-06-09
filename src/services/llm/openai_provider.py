"""OpenAI chat provider (LlmProvider 구현).

`openai` SDK 직접 호출을 이 한 파일로 캡슐화한다. 학습 루프 코드는
`LlmProvider` 인터페이스에만 의존하므로 추후 다른 백엔드로 교체 가능.
"""

from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from src.services.llm.base import ChatMessage, ChatResult


class OpenAIProvider:
    """AsyncOpenAI 기반 chat provider."""

    def __init__(self, api_key: str, *, client: AsyncOpenAI | None = None) -> None:
        # client 주입 가능 (테스트/모킹). 미지정 시 api_key로 생성.
        self._client = client or AsyncOpenAI(api_key=api_key)

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.0,
        response_format: dict[str, Any] | None = None,
    ) -> ChatResult:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format

        resp = await self._client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        usage = resp.usage
        return ChatResult(
            text=choice.message.content or "",
            model=resp.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
        )
