"""테스트용 Fake provider (LlmProvider 구현).

실 API 키 없이 학습 루프를 단위 테스트한다. 마지막 user 메시지 내용을 키로
결정적 응답을 돌려준다 — temperature와 무관하게 항상 같은 입력 → 같은 출력이므로
캐시 결정성(`llm_cache_hit` 1.0) 검증에 적합.
"""

from __future__ import annotations

from typing import Any

from src.services.llm.base import ChatMessage, ChatResult


class FakeProvider:
    """결정적 chat 응답을 돌려주는 테스트 더블."""

    def __init__(
        self,
        responses: dict[str, str] | None = None,
        *,
        default: str = '{"explanation": "FAKE", "examples": []}',
    ) -> None:
        # responses: 마지막 user content → 응답 텍스트 매핑 (미스 시 default)
        self.responses = responses or {}
        self.default = default
        # 호출 기록 (테스트에서 호출 횟수 검증용)
        self.calls: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.0,
        response_format: dict[str, Any] | None = None,
    ) -> ChatResult:
        self.calls.append(
            {
                "model": model,
                "temperature": temperature,
                "messages": [m.model_dump() for m in messages],
            }
        )
        user_text = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        text = self.responses.get(user_text, self.default)
        return ChatResult(
            text=text,
            model=model,
            prompt_tokens=len(user_text),
            completion_tokens=len(text),
        )

    @property
    def call_count(self) -> int:
        return len(self.calls)
