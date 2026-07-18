"""익명 세션 승격 통합 테스트 (세션 9 S6, 실DB E2E).

게스트 진단(익명 세션 + 진단 세션) → 회원가입(쿠키 동반) → 익명 세션이 새 계정에
연결되고(linked_user_id) 진단이 user.initial_diagnostic_session_id로 이전된다.
쿠키 없는 가입은 승격 없이 정상 동작. 생성 데이터는 정리.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.api.main import app
from src.core.config import settings
from src.db.session import get_session
from src.shared.auth.email import get_email_sender

_EMAIL = "promote_test@example.com"
_TOKEN = "sess_promote_test_cookie"


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


class _FakeEmailSender:
    async def send(self, *, to: str, subject: str, body: str) -> None:
        return None


def _override(engine: AsyncEngine) -> None:
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _dep() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _dep
    app.dependency_overrides[get_email_sender] = lambda: _FakeEmailSender()


async def _seed_guest_diagnostic(engine: AsyncEngine) -> str:
    """익명 세션 + 완료 진단 세션 시드. 진단 세션 id 반환."""
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
                    "(anonymous_session_id, mode, max_score, status) "
                    "VALUES (:a, 'initial_assessment', 10, 'completed') RETURNING id"
                ),
                {"a": anon_id},
            )
        ).scalar()
        await conn.execute(
            text(
                "UPDATE anonymous_sessions SET active_diagnostic_session_id = :d "
                "WHERE id = :a"
            ),
            {"d": diag_id, "a": anon_id},
        )
    return str(diag_id)


async def _cleanup(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        # 순환 FK 회피 — 포인터 먼저 NULL, 그 다음 삭제.
        await conn.execute(
            text("UPDATE users SET initial_diagnostic_session_id = NULL "
                 "WHERE email = :e"),
            {"e": _EMAIL},
        )
        await conn.execute(
            text("UPDATE anonymous_sessions SET active_diagnostic_session_id = NULL "
                 "WHERE session_token = :t"),
            {"t": _TOKEN},
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


def test_signup_with_cookie_promotes_guest_diagnostic() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override(engine)
        transport = ASGITransport(app=app)
        try:
            diag_id = await _seed_guest_diagnostic(engine)
            async with AsyncClient(
                transport=transport,
                base_url="http://t",
                cookies={"session_id": _TOKEN},
            ) as client:
                resp = await client.post(
                    "/api/v1/auth/signup",
                    json={
                        "email": _EMAIL,
                        "password": "abcd1234",
                        "nickname": "승격테스터",
                    },
                )
            assert resp.status_code == 201

            async with engine.connect() as conn:
                linked = (
                    await conn.execute(
                        text(
                            "SELECT a.linked_user_id, u.id, "
                            "u.initial_diagnostic_session_id "
                            "FROM anonymous_sessions a, users u "
                            "WHERE a.session_token = :t AND u.email = :e"
                        ),
                        {"t": _TOKEN, "e": _EMAIL},
                    )
                ).first()
            assert linked is not None
            linked_user_id, user_id, initial_diag = linked
            assert str(linked_user_id) == str(user_id)  # 익명 세션 → 계정 연결
            assert str(initial_diag) == diag_id  # 진단 이력 이전
        finally:
            app.dependency_overrides.clear()
            await _cleanup(engine)
            await engine.dispose()

    asyncio.run(flow())


def test_signup_without_cookie_no_promotion() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override(engine)
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                resp = await client.post(
                    "/api/v1/auth/signup",
                    json={
                        "email": _EMAIL,
                        "password": "abcd1234",
                        "nickname": "노쿠키",
                    },
                )
            assert resp.status_code == 201
            async with engine.connect() as conn:
                initial = (
                    await conn.execute(
                        text(
                            "SELECT initial_diagnostic_session_id "
                            "FROM users WHERE email = :e"
                        ),
                        {"e": _EMAIL},
                    )
                ).scalar()
            assert initial is None  # 승격 대상 없음 → NULL
        finally:
            app.dependency_overrides.clear()
            await _cleanup(engine)
            await engine.dispose()

    asyncio.run(flow())
