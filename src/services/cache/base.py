"""LLM 응답 캐시 추상화 + 캐시 키 전략.

캐시 키 전략 (plan §2-3):
    prompt_hash = sha256( canonical_json({
        task, grammar_point_id, level, chunk_keys(정렬), angle, template_version
    }) )
    cache_key = "{model}:{prompt_hash}"

- temperature=0 + 위 키 → 같은 입력은 항상 같은 캐시 엔트리 (`llm_cache_hit` 1.0).
- 재설명 다양성은 temperature가 아니라 `angle`로 확보 → angle별로 결정적 캐시.
- chunk_keys 포함 → RAG 결과가 바뀌면 캐시도 자동 무효화 (정확성).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol, runtime_checkable


def make_prompt_hash(payload: dict[str, Any]) -> str:
    """프롬프트 결정 입력 → sha256 hex (64자). 키 순서·언어 무관 결정적."""
    canonical = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def make_cache_key(model: str, prompt_hash: str) -> str:
    """`{model}:{prompt_hash}` — cache_key 컬럼(≤255) 내 길이."""
    return f"{model}:{prompt_hash}"


@runtime_checkable
class LlmCache(Protocol):
    """LLM 응답 캐시. DB / Redis / in-memory 구현이 이 인터페이스를 만족한다."""

    async def get(self, cache_key: str) -> str | None:
        """cache_key의 응답 텍스트. 없거나 만료 시 None."""
        ...

    async def set(
        self,
        cache_key: str,
        *,
        model: str,
        prompt_hash: str,
        response_text: str,
        token_usage: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        """응답을 캐시에 저장 (멱등 upsert). ttl_seconds=None 이면 무기한."""
        ...
