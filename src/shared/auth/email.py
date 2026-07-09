"""이메일 발송 추상화 (인증 인프라, 세션 9 §b / Q3 재현 위임).

한 인터페이스(EmailSender) 뒤에 백엔드를 갈아끼운다.
- dev: ConsoleEmailSender — 실제 발송 없이 확인 링크를 로그로 출력.
- 실발송: SmtpEmailSender — aiosmtplib(async)로 SMTP 서버 전송.
설정(settings.smtp_host)에 따라 get_email_sender()가 자동 선택한다.

이렇게 분리하는 이유 = 회원가입/재발송 서비스는 "send만 호출"하고 발송 수단(콘솔/SMTP)은
몰라도 된다. 테스트는 캡처용 가짜 sender를 끼워 실제 발송 없이 흐름을 검증한다.
"""

from __future__ import annotations

import logging
from email.message import EmailMessage
from typing import Protocol

import aiosmtplib

from src.core.config import settings

logger = logging.getLogger(__name__)


class EmailSender(Protocol):
    """발송 계약. `send`를 가진 어떤 객체든 이 타입으로 통한다(구조적 타이핑)."""

    async def send(self, *, to: str, subject: str, body: str) -> None: ...


def build_message(*, to: str, subject: str, body: str, sender: str) -> EmailMessage:
    """표준 라이브러리 EmailMessage 조립(From/To/Subject/본문). 백엔드 공용."""
    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    return message


class ConsoleEmailSender:
    """dev 백엔드 — 발송하지 않고 본문을 로그로 남긴다(확인 링크 눈으로 확인)."""

    def __init__(self, sender: str) -> None:
        self._sender = sender

    async def send(self, *, to: str, subject: str, body: str) -> None:
        logger.info(
            "[email:console] from=%s to=%s subject=%s\n%s",
            self._sender,
            to,
            subject,
            body,
        )


class SmtpEmailSender:
    """실 발송 백엔드 — aiosmtplib로 SMTP 전송(async I/O)."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        use_tls: bool,
        sender: str,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._use_tls = use_tls
        self._sender = sender

    async def send(self, *, to: str, subject: str, body: str) -> None:
        message = build_message(
            to=to, subject=subject, body=body, sender=self._sender
        )
        await aiosmtplib.send(
            message,
            hostname=self._host,
            port=self._port,
            username=self._username,
            password=self._password,
            start_tls=self._use_tls,
        )


def get_email_sender() -> EmailSender:
    """설정 기반 백엔드 선택. SMTP host가 있으면 실 발송, 없으면 콘솔(dev)."""
    if settings.smtp_host:
        return SmtpEmailSender(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
            sender=settings.email_from,
        )
    return ConsoleEmailSender(sender=settings.email_from)
