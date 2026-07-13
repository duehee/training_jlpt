"""로그인 API 통합 테스트 (세션 9 S4-②, 실DB E2E).

성공(200 + JWT sub=user.id) / 틀린 비번(401) / 없는 이메일(401, 동일 메시지) /
OAuth 전용 계정(password_hash NULL) 비번 로그인 차단(401). 생성 데이터는 정리.
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
from src.shared.auth.jwt import get_subject

_EMAIL = "login_test@example.com"
_PASSWORD = "abcd1234"


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


def _override_get_session(engine: AsyncEngine) -> None:
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _dep() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _dep


async def _delete_email(engine: AsyncEngine, email: str) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE email = :e"), {"e": email})


async def _signup(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": _EMAIL, "password": _PASSWORD, "nickname": "로그인테스터"},
    )
    assert resp.status_code == 201


async def _mark_verified(engine: AsyncEngine, email: str) -> None:
    """로그인 게이팅(미인증 차단) 우회 — 확인 완료 상태로 만든다."""
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE users SET email_verified = true WHERE email = :e"),
            {"e": email},
        )


def test_login_success_returns_valid_jwt() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                await _signup(client)
                await _mark_verified(engine, _EMAIL)
                resp = await client.post(
                    "/api/v1/auth/login",
                    json={"email": _EMAIL, "password": _PASSWORD},
                )
            assert resp.status_code == 200
            body = resp.json()
            assert body["token_type"] == "bearer"
            token = body["access_token"]
            # 토큰이 실제로 유효하고 sub이 로그인한 유저를 가리키는지 확인.
            async with engine.connect() as conn:
                user_id = (
                    await conn.execute(
                        text("SELECT id FROM users WHERE email = :e"), {"e": _EMAIL}
                    )
                ).scalar()
            assert get_subject(token) == str(user_id)
        finally:
            app.dependency_overrides.pop(get_session, None)
            await _delete_email(engine, _EMAIL)
            await engine.dispose()

    asyncio.run(flow())


def test_login_wrong_password_401() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                await _signup(client)
                resp = await client.post(
                    "/api/v1/auth/login",
                    json={"email": _EMAIL, "password": "wrong9999"},
                )
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.pop(get_session, None)
            await _delete_email(engine, _EMAIL)
            await engine.dispose()

    asyncio.run(flow())


def test_login_unverified_blocked_403() -> None:
    """이메일 미확인 계정은 비번이 맞아도 로그인 차단(403, 정빈님 결정 B)."""

    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                await _signup(client)  # email_verified=False 상태
                resp = await client.post(
                    "/api/v1/auth/login",
                    json={"email": _EMAIL, "password": _PASSWORD},
                )
            assert resp.status_code == 403
            assert "이메일 확인" in resp.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_session, None)
            await _delete_email(engine, _EMAIL)
            await engine.dispose()

    asyncio.run(flow())


def test_login_unknown_email_401_same_message() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                resp = await client.post(
                    "/api/v1/auth/login",
                    json={"email": "nobody@example.com", "password": _PASSWORD},
                )
            assert resp.status_code == 401
            # 계정 존재 여부 비노출 — 틀린 비번과 동일한 메시지.
            assert resp.json()["detail"] == "이메일 또는 비밀번호가 올바르지 않습니다."
        finally:
            app.dependency_overrides.pop(get_session, None)
            await engine.dispose()

    asyncio.run(flow())


def test_login_oauth_only_account_blocked() -> None:
    """password_hash가 NULL인 계정(OAuth 전용)은 비밀번호 로그인 불가(401)."""

    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        transport = ASGITransport(app=app)
        try:
            # 비밀번호 없는 사용자 직접 삽입(OAuth 전용 시뮬레이션).
            async with engine.begin() as conn:
                await conn.execute(
                    text(
                        "INSERT INTO users (nickname, email, email_verified) "
                        "VALUES ('소셜', :e, true)"
                    ),
                    {"e": _EMAIL},
                )
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                resp = await client.post(
                    "/api/v1/auth/login",
                    json={"email": _EMAIL, "password": _PASSWORD},
                )
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.pop(get_session, None)
            await _delete_email(engine, _EMAIL)
            await engine.dispose()

    asyncio.run(flow())
