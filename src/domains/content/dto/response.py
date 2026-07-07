"""컨텐트(content) 응답 DTO — 문법 청크 검색 결과.

RAG 검색(retrieve) 결과 1건. 순수 계약 — 도메인 로직/ORM import 금지(규칙 2).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    """retrieval 결과 1건 (프롬프트·캐시 키 입력)."""

    chunk_key: str
    chunk_type: str
    body: dict[str, Any]
