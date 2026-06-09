"""LLM provider 추상화 (Protocol).

CLAUDE.md §과거 실패: "`openai` 라이브러리 직접 호출 → provider 추상화 사용".
런타임 학습 루프의 모든 chat 호출은 이 `LlmProvider` 인터페이스에만 의존한다.
구현체(`OpenAIProvider`)와 테스트 더블(`FakeProvider`)이 이 Protocol을 만족한다.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """단일 chat 메시지."""

    role: str  # "system" | "user" | "assistant"
    content: str


class ChatResult(BaseModel):
    """chat 호출 결과 (텍스트 + 사용량)."""

    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


@runtime_checkable
class LlmProvider(Protocol):
    """chat 생성 provider. 구조 타이핑 — 상속 불필요."""

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.0,
        response_format: dict[str, Any] | None = None,
    ) -> ChatResult:
        """messages로 chat 응답을 생성한다.

        temperature=0.0 이 기본 — 캐시 결정성(`llm_cache_hit` 1.0)을 위해
        캐시 대상 경로는 항상 0을 사용한다.
        """
        ...
