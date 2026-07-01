"""In-memory LLM 캐시 (LlmCache 구현).

DB 없이 단위 테스트·eval에서 사용한다. DB 캐시와 동일 Protocol을 만족하므로
학습 루프 코드는 둘을 구분하지 않는다.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryLlmCache:
    """프로세스 메모리 기반 캐시 (테스트/eval용)."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, datetime | None]] = {}

    async def get(self, cache_key: str) -> str | None:
        entry = self._store.get(cache_key)
        if entry is None:
            return None
        response_text, expires_at = entry
        if expires_at is not None and expires_at <= _now():
            del self._store[cache_key]
            return None
        return response_text

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
        expires_at = None if ttl_seconds is None else _now() + timedelta(
            seconds=ttl_seconds
        )
        self._store[cache_key] = (response_text, expires_at)
