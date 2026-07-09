"""회원가입 API 통합 테스트 (세션 9 S4-①, 실DB E2E).

가입 성공(201) / 이메일 중복(409) / 약한 비밀번호(400) / 이메일 형식(422) +
password_hash 비노출 + DB에 해시로 저장(평문 X). 생성 데이터는 종료 시 정리.

engine 관리는 test_web_routes.py 패턴 계승 — NullPool 테스트 engine을 get_session
의존성 override로 주입하고, 테스트당 단일 asyncio.run + finally dispose로 전역 풀
오염(닫힌 루프 재사용)을 피한다.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

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

_TEST_EMAIL = "signup_test@example.com"


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


def test_signup_success_then_cleanup() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                resp = await client.post(
                    "/api/v1/auth/signup",
                    json={
                        "email": _TEST_EMAIL,
                        "password": "abcd1234",
                        "nickname": "테스터",
                    },
                )
            assert resp.status_code == 201
            body = resp.json()
            assert body["email"] == _TEST_EMAIL
            assert body["nickname"] == "테스터"
            assert body["email_verified"] is False
            assert "password_hash" not in body  # 해시 비노출
            assert "password" not in body

            # DB에 평문이 아니라 bcrypt 해시로 저장됐는지 확인.
            async with engine.connect() as conn:
                row = (
                    await conn.execute(
                        text("SELECT password_hash FROM users WHERE email = :e"),
                        {"e": _TEST_EMAIL},
                    )
                ).first()
            assert row is not None
            stored = row[0]
            assert stored != "abcd1234"  # 평문 저장 금지
            assert stored.startswith("$2")  # bcrypt 해시 시그니처
        finally:
            app.dependency_overrides.pop(get_session, None)
            await _delete_email(engine, _TEST_EMAIL)
            await engine.dispose()

    asyncio.run(flow())


def test_signup_duplicate_email_conflict() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                payload: dict[str, Any] = {
                    "email": _TEST_EMAIL,
                    "password": "abcd1234",
                    "nickname": "테스터",
                }
                first = await client.post("/api/v1/auth/signup", json=payload)
                assert first.status_code == 201
                dup = await client.post(
                    "/api/v1/auth/signup",
                    json={**payload, "nickname": "다른사람"},
                )
            assert dup.status_code == 409
        finally:
            app.dependency_overrides.pop(get_session, None)
            await _delete_email(engine, _TEST_EMAIL)
            await engine.dispose()

    asyncio.run(flow())


def test_signup_weak_password_rejected() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                resp = await client.post(
                    "/api/v1/auth/signup",
                    json={
                        "email": "weak_pw@example.com",
                        "password": "short",
                        "nickname": "테스터",
                    },
                )
            assert resp.status_code == 400
            assert "8자" in resp.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_session, None)
            await engine.dispose()

    asyncio.run(flow())


def test_signup_invalid_email_rejected() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                resp = await client.post(
                    "/api/v1/auth/signup",
                    json={
                        "email": "not-an-email",
                        "password": "abcd1234",
                        "nickname": "테스터",
                    },
                )
            assert resp.status_code == 422  # pydantic DTO 검증 실패
        finally:
            app.dependency_overrides.pop(get_session, None)
            await engine.dispose()

    asyncio.run(flow())
