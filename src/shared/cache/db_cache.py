"""DB 기반 LLM 응답 캐시 (`llm_response_cache` 테이블).

plan §2-2: Stage 1 = DB 단독 (L2/영속/단일 진실). Redis L1은 Stage 6.

설계 결정 (lead 사후 보고 대상): 캐시 `set`은 비즈니스 트랜잭션과 분리해
자체 commit 한다 (best-effort 독립). 이유 — 학습 흐름 도중 비즈니스 로직이
롤백돼도 이미 생성·과금된 LLM 응답은 보존돼야 재호출 비용을 막는다.
이 때문에 `DbLlmCache`는 호출자 세션이 아니라 전용 sessionmaker로 동작한다.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.db.models import LlmResponseCache


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DbLlmCache:
    """`llm_response_cache` 테이블 기반 캐시."""

    def __init__(self, session_factory: async_sessionmaker[Any]) -> None:
        # 캐시는 비즈니스 트랜잭션과 분리 → 전용 세션 팩토리로 독립 commit.
        self._session_factory = session_factory

    async def get(self, cache_key: str) -> str | None:
        async with self._session_factory() as session:
            stmt = select(
                LlmResponseCache.response_text, LlmResponseCache.expires_at
            ).where(LlmResponseCache.cache_key == cache_key)
            row = (await session.execute(stmt)).first()
        if row is None:
            return None
        response_text, expires_at = row
        if expires_at is not None and expires_at <= _now():
            return None
        return str(response_text)

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
        stmt = pg_insert(LlmResponseCache).values(
            cache_key=cache_key,
            prompt_hash=prompt_hash,
            model_name=model,
            response_text=response_text,
            token_usage=token_usage,
            expires_at=expires_at,
        )
        # 멱등: 같은 cache_key 재기록 시 응답·사용량·만료 갱신.
        stmt = stmt.on_conflict_do_update(
            index_elements=["cache_key"],
            set_={
                "response_text": response_text,
                "model_name": model,
                "prompt_hash": prompt_hash,
                "token_usage": token_usage,
                "expires_at": expires_at,
            },
        )
        async with self._session_factory() as session:
            await session.execute(stmt)
            await session.commit()
