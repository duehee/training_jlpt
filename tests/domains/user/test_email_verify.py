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
