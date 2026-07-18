"""OAuth 계정 upsert 서비스 테스트 (세션 9 S8-①, 실DB E2E).

신규(user+oauth_account 생성) / 재로그인(같은 계정 반환) / 이메일 통합(기존 user에 연결).
Google 호출은 없음 — 서비스 계층(oauth_upsert_user)만 직접 검증.
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
from src.domains.user.service import oauth_upsert_user
from src.shared.auth.oauth import GoogleUser, get_google_oauth_client

_EMAIL = "oauth_test@example.com"


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


def _sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def _cleanup(engine: AsyncEngine) -> None:
    # oauth_accounts는 users FK CASCADE로 함께 삭제.
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE email = :e"), {"e": _EMAIL})


def test_oauth_new_user_creates_account() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        factory = _sessionmaker(engine)
        try:
            async with factory() as session:
                user = await oauth_upsert_user(
                    session,
                    provider="google",
                    provider_account_id="google-sub-111",
                    email=_EMAIL,
                    name="구글유저",
                )
                assert user.email == _EMAIL
                assert user.nickname == "구글유저"
                assert user.password_hash is None  # 소셜 전용
                assert user.email_verified is True  # provider 검증

            # oauth_accounts 1건 연결됐는지 확인
            async with engine.connect() as conn:
                cnt = (
                    await conn.execute(
                        text(
                            "SELECT count(*) FROM oauth_accounts o "
                            "JOIN users u ON u.id = o.user_id WHERE u.email = :e"
                        ),
                        {"e": _EMAIL},
                    )
                ).scalar()
            assert cnt == 1
        finally:
            await _cleanup(engine)
            await engine.dispose()

    asyncio.run(flow())


def test_oauth_existing_account_returns_same_user() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        factory = _sessionmaker(engine)
        try:
            async with factory() as session:
                first = await oauth_upsert_user(
                    session,
                    provider="google",
                    provider_account_id="google-sub-222",
                    email=_EMAIL,
                    name="구글유저",
                )
                first_id = first.id
            async with factory() as session:
                second = await oauth_upsert_user(
                    session,
                    provider="google",
                    provider_account_id="google-sub-222",
                    email=_EMAIL,
                    name="구글유저",
                )
                assert second.id == first_id  # 같은 계정

            # oauth_accounts 중복 생성 안 됨(여전히 1건)
            async with engine.connect() as conn:
                cnt = (
                    await conn.execute(
                        text(
                            "SELECT count(*) FROM oauth_accounts o "
                            "JOIN users u ON u.id = o.user_id WHERE u.email = :e"
                        ),
                        {"e": _EMAIL},
                    )
                ).scalar()
            assert cnt == 1
        finally:
            await _cleanup(engine)
            await engine.dispose()

    asyncio.run(flow())


class _FakeGoogleClient:
    """실제 Google 호출 대신 고정 사용자를 반환하는 가짜 클라이언트."""

    async def exchange_code(self, code: str) -> GoogleUser:
        return GoogleUser(sub="google-sub-callback", email=_EMAIL, name="콜백유저")


def _override_session(engine: AsyncEngine) -> None:
    factory = _sessionmaker(engine)

    async def _dep() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = _dep


def test_google_authorize_redirects_with_state_cookie() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_session(engine)
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(
                transport=transport, base_url="http://t", follow_redirects=False
            ) as client:
                resp = await client.get("/api/v1/auth/google")
            assert resp.status_code in (302, 307)
            assert "accounts.google.com" in resp.headers["location"]
            assert "oauth_state=" in resp.headers.get("set-cookie", "")
        finally:
            app.dependency_overrides.clear()
            await engine.dispose()

    asyncio.run(flow())


def test_google_callback_success_sets_jwt_and_redirects() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_session(engine)
        app.dependency_overrides[get_google_oauth_client] = lambda: _FakeGoogleClient()
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(
                transport=transport,
                base_url="http://t",
                follow_redirects=False,
                cookies={"oauth_state": "state-xyz"},
            ) as client:
                resp = await client.get(
                    "/api/v1/auth/google/callback?code=abc&state=state-xyz"
                )
            assert resp.status_code == 303
            assert resp.headers["location"] == "/mypage"
            assert "access_token=" in resp.headers.get("set-cookie", "")

            async with engine.connect() as conn:
                cnt = (
                    await conn.execute(
                        text("SELECT count(*) FROM users WHERE email = :e"),
                        {"e": _EMAIL},
                    )
                ).scalar()
            assert cnt == 1  # OAuth 사용자 생성됨
        finally:
            app.dependency_overrides.clear()
            await _cleanup(engine)
            await engine.dispose()

    asyncio.run(flow())


def test_google_callback_state_mismatch_400() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_session(engine)
        app.dependency_overrides[get_google_oauth_client] = lambda: _FakeGoogleClient()
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(
                transport=transport,
                base_url="http://t",
                follow_redirects=False,
                cookies={"oauth_state": "cookie-state"},
            ) as client:
                resp = await client.get(
                    "/api/v1/auth/google/callback?code=abc&state=query-state"
                )
            assert resp.status_code == 400  # state 불일치(CSRF 방어)
        finally:
            app.dependency_overrides.clear()
            await engine.dispose()

    asyncio.run(flow())


def test_oauth_links_to_existing_email_user() -> None:
    """같은 이메일의 기존(비번) 계정이 있으면 새 user 만들지 않고 연결."""

    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        factory = _sessionmaker(engine)
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text(
                        "INSERT INTO users (nickname, email, email_verified) "
                        "VALUES ('기존', :e, true)"
                    ),
                    {"e": _EMAIL},
                )
                existing_id = (
                    await conn.execute(
                        text("SELECT id FROM users WHERE email = :e"), {"e": _EMAIL}
                    )
                ).scalar()

            async with factory() as session:
                user = await oauth_upsert_user(
                    session,
                    provider="google",
                    provider_account_id="google-sub-333",
                    email=_EMAIL,
                    name="구글유저",
                )
                assert str(user.id) == str(existing_id)  # 새 user 생성 X

            async with engine.connect() as conn:
                user_cnt = (
                    await conn.execute(
                        text("SELECT count(*) FROM users WHERE email = :e"),
                        {"e": _EMAIL},
                    )
                ).scalar()
            assert user_cnt == 1  # 이메일당 user 1개 유지
        finally:
            await _cleanup(engine)
            await engine.dispose()

    asyncio.run(flow())
