"""마이페이지 dashboard 데이터 조회 (세션 9 ④, 실DB E2E).

진단 이력 있는 사용자 → 저장된 레벨/점수 실데이터 / 없는 사용자 → has_diagnostic=False.
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
from src.domains.user.service import get_user_by_id, get_user_dashboard

_EMAIL = "dashboard_test@example.com"
_TOKEN = "sess_dashboard_test"


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


async def _seed_user_with_diagnostic(engine: AsyncEngine) -> str:
    """user + 익명세션 + 완료 진단 + user.initial 연결. user id 반환."""
    async with engine.begin() as conn:
        anon_id = (
            await conn.execute(
                text(
                    "INSERT INTO anonymous_sessions (session_token, expires_at) "
                    "VALUES (:t, now() + interval '1 day') RETURNING id"
                ),
                {"t": _TOKEN},
            )
        ).scalar()
        diag_id = (
            await conn.execute(
                text(
                    "INSERT INTO diagnostic_sessions "
                    "(anonymous_session_id, mode, max_score, score, "
                    "diagnosed_level, status) "
                    "VALUES (:a, 'initial_assessment', 10, 8, 'N5', 'completed') "
                    "RETURNING id"
                ),
                {"a": anon_id},
            )
        ).scalar()
        uid = (
            await conn.execute(
                text(
                    "INSERT INTO users "
                    "(nickname, email, email_verified, initial_diagnostic_session_id) "
                    "VALUES ('대시', :e, true, :d) RETURNING id"
                ),
                {"e": _EMAIL, "d": diag_id},
            )
        ).scalar()
    return str(uid)


async def _seed_user_no_diagnostic(engine: AsyncEngine) -> str:
    async with engine.begin() as conn:
        uid = (
            await conn.execute(
                text(
                    "INSERT INTO users (nickname, email, email_verified) "
                    "VALUES ('노진단', :e, true) RETURNING id"
                ),
                {"e": _EMAIL},
            )
        ).scalar()
    return str(uid)


async def _cleanup(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE users SET initial_diagnostic_session_id = NULL "
                 "WHERE email = :e"),
            {"e": _EMAIL},
        )
        await conn.execute(
            text("DELETE FROM diagnostic_sessions WHERE anonymous_session_id = "
                 "(SELECT id FROM anonymous_sessions WHERE session_token = :t)"),
            {"t": _TOKEN},
        )
        await conn.execute(
            text("DELETE FROM anonymous_sessions WHERE session_token = :t"),
            {"t": _TOKEN},
        )
        await conn.execute(text("DELETE FROM users WHERE email = :e"), {"e": _EMAIL})


def test_dashboard_with_diagnostic_returns_real_data() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        try:
            uid = await _seed_user_with_diagnostic(engine)
            async with _factory(engine)() as session:
                user = await get_user_by_id(session, uuid.UUID(uid))
                assert user is not None
                data = await get_user_dashboard(session, user)
                assert data.has_diagnostic is True
                assert data.diagnosed_level == "N5"
                assert data.score == 8
                assert data.max_score == 10
                assert data.nickname == "대시"
        finally:
            await _cleanup(engine)
            await engine.dispose()

    asyncio.run(flow())


def test_dashboard_without_diagnostic() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        try:
            uid = await _seed_user_no_diagnostic(engine)
            async with _factory(engine)() as session:
                user = await get_user_by_id(session, uuid.UUID(uid))
                assert user is not None
                data = await get_user_dashboard(session, user)
                assert data.has_diagnostic is False
                assert data.diagnosed_level is None
        finally:
            await _cleanup(engine)
            await engine.dispose()

    asyncio.run(flow())
