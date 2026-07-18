"""User 조회 + 토큰→User 해석 (세션 9 S7-③, 하린 SSR 보호라우트용, 실DB E2E).

get_user_by_id / resolve_user_from_token — 유효 토큰→User, 무효·만료·비UUID→None.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.core.config import settings
from src.domains.user.service import get_user_by_id, resolve_user_from_token
from src.shared.auth.jwt import create_access_token

_EMAIL = "resolve_test@example.com"


def _db_available() -> bool:
    async def _ping() -> bool:
        eng = create_async_engine(settings.database_url, poolclass=NullPool)
        try:
            async with eng.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
        finally:
            await eng.dispose()

    try:
        return asyncio.run(_ping())
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _db_available(), reason="DB 미가용 (통합 테스트 skip)"
)


def _factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def _seed_user(engine: AsyncEngine) -> str:
    async with engine.begin() as conn:
        uid = (
            await conn.execute(
                text(
                    "INSERT INTO users (nickname, email, email_verified) "
                    "VALUES ('해석', :e, true) RETURNING id"
                ),
                {"e": _EMAIL},
            )
        ).scalar()
    return str(uid)


async def _cleanup(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE email = :e"), {"e": _EMAIL})


def test_get_user_by_id_found_and_missing() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        try:
            uid = await _seed_user(engine)
            async with _factory(engine)() as session:
                found = await get_user_by_id(session, uuid.UUID(uid))
                assert found is not None and found.email == _EMAIL
                missing = await get_user_by_id(session, uuid.uuid4())
                assert missing is None
        finally:
            await _cleanup(engine)
            await engine.dispose()

    asyncio.run(flow())


def test_resolve_valid_token_returns_user() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        try:
            uid = await _seed_user(engine)
            token = create_access_token(subject=uid)
            async with _factory(engine)() as session:
                user = await resolve_user_from_token(session, token)
                assert user is not None and str(user.id) == uid
        finally:
            await _cleanup(engine)
            await engine.dispose()

    asyncio.run(flow())


def test_resolve_invalid_or_expired_token_returns_none() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        try:
            async with _factory(engine)() as session:
                assert await resolve_user_from_token(session, "garbage") is None
                # 만료 토큰
                expired = create_access_token(subject=str(uuid.uuid4()), expires_minutes=-1)
                assert await resolve_user_from_token(session, expired) is None
                # sub이 UUID가 아닌 토큰
                non_uuid = create_access_token(subject="not-a-uuid")
                assert await resolve_user_from_token(session, non_uuid) is None
        finally:
            await engine.dispose()

    asyncio.run(flow())
