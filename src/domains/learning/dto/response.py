"""학습(learning) 응답 DTO — 설명 생성 결과.

순수 계약 — 도메인 로직/ORM import 금지(규칙 2).
"""

from __future__ import annotations

from pydantic import BaseModel


class ExplanationResult(BaseModel):
    """설명 생성 결과."""

    text: str  # JSON 문자열 ({explanation, examples[]})
    cached: bool
    model: str
    cache_key: str
    angle: int
    chunk_keys: list[str]
