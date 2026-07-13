"""이메일 확인 흐름 테스트 — S5-① 토큰 발급 + 메일 발송 연동 (실DB E2E).

가입 시: 확인 토큰 1건이 DB에 해시로 저장되고, 확인 링크가 담긴 메일이 발송된다.
EmailSender는 FakeEmailSender(구조적 타이핑 — 상속 없이 send만)로 교체해 캡처한다.
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
from src.shared.auth.tokens import hash_token

_EMAIL = "verify_test@example.com"
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


class FakeEmailSender:
    """캡처용 가짜 sender. EmailSender를 상속하지 않아도 send만 있으면 통한다."""

    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    async def send(self, *, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


def _override_get_session(engine: AsyncEngine) -> None:
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _dep() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _dep


async def _delete_email(engine: AsyncEngine, email: str) -> None:
    # email_verification_tokens는 users FK CASCADE로 함께 삭제된다.
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE email = :e"), {"e": email})


def test_signup_issues_token_and_sends_email() -> None:
    fake = FakeEmailSender()

    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        app.dependency_overrides[get_email_sender] = lambda: fake
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                resp = await client.post(
                    "/api/v1/auth/signup",
                    json={
                        "email": _EMAIL,
                        "password": _PASSWORD,
                        "nickname": "확인테스터",
                    },
                )
            assert resp.status_code == 201

            # 1) 메일 1통 발송 + 확인 링크 포함
            assert len(fake.sent) == 1
            msg = fake.sent[0]
            assert msg["to"] == _EMAIL
            assert "/api/v1/auth/verify?token=" in msg["body"]

            # 2) 링크의 raw 토큰을 해시하면 DB에 저장된 토큰과 일치
            raw = msg["body"].split("token=")[1].split()[0]
            async with engine.connect() as conn:
                row = (
                    await conn.execute(
                        text(
                            "SELECT t.token_hash, t.consumed_at, t.expires_at "
                            "FROM email_verification_tokens t "
                            "JOIN users u ON u.id = t.user_id "
                            "WHERE u.email = :e"
                        ),
                        {"e": _EMAIL},
                    )
                ).all()
            assert len(row) == 1
            token_hash, consumed_at, expires_at = row[0]
            assert token_hash == hash_token(raw)  # DB엔 해시만, raw 아님
            assert consumed_at is None  # 아직 미사용
            assert expires_at is not None  # 만료 설정됨
        finally:
            app.dependency_overrides.pop(get_session, None)
            app.dependency_overrides.pop(get_email_sender, None)
            await _delete_email(engine, _EMAIL)
            await engine.dispose()

    asyncio.run(flow())


async def _signup_capture_token(
    client: AsyncClient, fake: FakeEmailSender
) -> str:
    """가입 후 발송 메일에서 raw 확인 토큰을 추출."""
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": _EMAIL, "password": _PASSWORD, "nickname": "확인테스터"},
    )
    assert resp.status_code == 201
    return fake.sent[0]["body"].split("token=")[1].split()[0]


def test_verify_success_sets_email_verified() -> None:
    fake = FakeEmailSender()

    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        app.dependency_overrides[get_email_sender] = lambda: fake
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                raw = await _signup_capture_token(client, fake)
                resp = await client.get(f"/api/v1/auth/verify?token={raw}")
                assert resp.status_code == 200
                assert resp.json()["email"] == _EMAIL

                # 두 번째 클릭(재사용) → 소비된 토큰이라 400
                again = await client.get(f"/api/v1/auth/verify?token={raw}")
                assert again.status_code == 400

            # DB: email_verified True + 토큰 consumed
            async with engine.connect() as conn:
                verified = (
                    await conn.execute(
                        text("SELECT email_verified FROM users WHERE email = :e"),
                        {"e": _EMAIL},
                    )
                ).scalar()
                consumed = (
                    await conn.execute(
                        text(
                            "SELECT t.consumed_at FROM email_verification_tokens t "
                            "JOIN users u ON u.id = t.user_id WHERE u.email = :e"
                        ),
                        {"e": _EMAIL},
                    )
                ).scalar()
            assert verified is True
            assert consumed is not None
        finally:
            app.dependency_overrides.pop(get_session, None)
            app.dependency_overrides.pop(get_email_sender, None)
            await _delete_email(engine, _EMAIL)
            await engine.dispose()

    asyncio.run(flow())


def test_resend_invalidates_old_and_sends_new() -> None:
    """재발송 → 옛 링크 폐기(400) + 새 링크로 확인 성공."""
    fake = FakeEmailSender()

    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        app.dependency_overrides[get_email_sender] = lambda: fake
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                old_raw = await _signup_capture_token(client, fake)  # sent[0]
                resend = await client.post(
                    "/api/v1/auth/verify/resend", json={"email": _EMAIL}
                )
                assert resend.status_code == 200
                assert len(fake.sent) == 2  # 가입 1 + 재발송 1
                new_raw = fake.sent[1]["body"].split("token=")[1].split()[0]

                # 옛 링크는 무효(400), 새 링크는 성공(200)
                old_resp = await client.get(f"/api/v1/auth/verify?token={old_raw}")
                assert old_resp.status_code == 400
                new_resp = await client.get(f"/api/v1/auth/verify?token={new_raw}")
                assert new_resp.status_code == 200
        finally:
            app.dependency_overrides.pop(get_session, None)
            app.dependency_overrides.pop(get_email_sender, None)
            await _delete_email(engine, _EMAIL)
            await engine.dispose()

    asyncio.run(flow())


def test_resend_no_email_when_already_verified() -> None:
    """이미 확인된 계정 재발송 → 발송 없음, 응답은 동일(200)."""
    fake = FakeEmailSender()

    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        app.dependency_overrides[get_email_sender] = lambda: fake
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                await _signup_capture_token(client, fake)  # sent[0]
                async with engine.begin() as conn:
                    await conn.execute(
                        text(
                            "UPDATE users SET email_verified = true WHERE email = :e"
                        ),
                        {"e": _EMAIL},
                    )
                resend = await client.post(
                    "/api/v1/auth/verify/resend", json={"email": _EMAIL}
                )
            assert resend.status_code == 200
            assert len(fake.sent) == 1  # 재발송 없음(가입 1통뿐)
        finally:
            app.dependency_overrides.pop(get_session, None)
            app.dependency_overrides.pop(get_email_sender, None)
            await _delete_email(engine, _EMAIL)
            await engine.dispose()

    asyncio.run(flow())


def test_resend_unknown_email_same_response_no_send() -> None:
    """미존재 이메일 재발송 → 발송 없음, 응답은 동일(200, 계정 비노출)."""
    fake = FakeEmailSender()

    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        app.dependency_overrides[get_email_sender] = lambda: fake
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                resend = await client.post(
                    "/api/v1/auth/verify/resend",
                    json={"email": "ghost@example.com"},
                )
            assert resend.status_code == 200
            assert len(fake.sent) == 0
        finally:
            app.dependency_overrides.pop(get_session, None)
            app.dependency_overrides.pop(get_email_sender, None)
            await engine.dispose()

    asyncio.run(flow())


def test_verify_invalid_token_400() -> None:
    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                resp = await client.get("/api/v1/auth/verify?token=nonexistent")
            assert resp.status_code == 400
        finally:
            app.dependency_overrides.pop(get_session, None)
            await engine.dispose()

    asyncio.run(flow())


def test_verify_expired_token_410() -> None:
    """만료된 토큰(과거 expires_at)은 410으로 재발송을 유도한다."""
    fake = FakeEmailSender()

    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        app.dependency_overrides[get_email_sender] = lambda: fake
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://t") as client:
                raw = await _signup_capture_token(client, fake)
                # 토큰을 과거로 만료시킨다.
                async with engine.begin() as conn:
                    await conn.execute(
                        text(
                            "UPDATE email_verification_tokens "
                            "SET expires_at = now() - interval '1 hour' "
                            "WHERE user_id = (SELECT id FROM users WHERE email = :e)"
                        ),
                        {"e": _EMAIL},
                    )
                resp = await client.get(f"/api/v1/auth/verify?token={raw}")
            assert resp.status_code == 410
        finally:
            app.dependency_overrides.pop(get_session, None)
            app.dependency_overrides.pop(get_email_sender, None)
            await _delete_email(engine, _EMAIL)
            await engine.dispose()

    asyncio.run(flow())
