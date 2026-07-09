"""EmailSender 추상화 단위 테스트 (세션 9 S3-③).

메시지 조립 / 콘솔 백엔드 / 실 SMTP 백엔드(aiosmtplib mock) / 설정 기반 팩토리 전환.
프로젝트 async 테스트 컨벤션(asyncio.run)에 맞춤.
"""

from __future__ import annotations

import asyncio
import logging
from email.message import EmailMessage
from typing import Any

import pytest

from src.core.config import settings
from src.shared.auth import email as email_mod
from src.shared.auth.email import (
    ConsoleEmailSender,
    SmtpEmailSender,
    build_message,
    get_email_sender,
)


def test_build_message_sets_headers_and_body() -> None:
    msg = build_message(
        to="u@example.com", subject="확인", body="링크", sender="no-reply@x"
    )
    assert msg["To"] == "u@example.com"
    assert msg["From"] == "no-reply@x"
    assert msg["Subject"] == "확인"
    assert "링크" in msg.get_content()


def test_console_sender_logs_and_does_not_raise(
    caplog: pytest.LogCaptureFixture,
) -> None:
    sender = ConsoleEmailSender(sender="no-reply@x")
    with caplog.at_level(logging.INFO, logger="src.shared.auth.email"):
        asyncio.run(
            sender.send(to="u@example.com", subject="확인 메일", body="click here")
        )
    assert "u@example.com" in caplog.text
    assert "확인 메일" in caplog.text


def test_smtp_sender_calls_aiosmtplib(monkeypatch: pytest.MonkeyPatch) -> None:
    """실 SMTP 백엔드는 aiosmtplib.send를 올바른 인자로 호출한다(실제 발송 X)."""
    captured: dict[str, Any] = {}

    async def fake_send(message: EmailMessage, **kwargs: Any) -> None:
        captured["message"] = message
        captured["kwargs"] = kwargs

    monkeypatch.setattr(email_mod.aiosmtplib, "send", fake_send)

    sender = SmtpEmailSender(
        host="smtp.example.com",
        port=587,
        username="user",
        password="pw",
        use_tls=True,
        sender="no-reply@x",
    )
    asyncio.run(sender.send(to="u@example.com", subject="s", body="b"))

    kwargs = captured["kwargs"]
    assert kwargs["hostname"] == "smtp.example.com"
    assert kwargs["port"] == 587
    assert kwargs["username"] == "user"
    assert kwargs["start_tls"] is True


def test_factory_returns_console_without_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "smtp_host", None)
    assert isinstance(get_email_sender(), ConsoleEmailSender)


def test_factory_returns_smtp_with_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    assert isinstance(get_email_sender(), SmtpEmailSender)
