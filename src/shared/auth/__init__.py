"""인증 인프라 패키지 (세션 9).

도메인-무관 인증 유틸: 비밀번호 해싱/정책, (예정) JWT, EmailSender, OAuth 클라이언트.
"""

from __future__ import annotations

from src.shared.auth.email import (
    ConsoleEmailSender,
    EmailSender,
    SmtpEmailSender,
    build_message,
    get_email_sender,
)
from src.shared.auth.jwt import (
    create_access_token,
    decode_access_token,
    get_subject,
)
from src.shared.auth.password import (
    PASSWORD_MIN_LENGTH,
    hash_password,
    validate_password_policy,
    verify_password,
)

__all__ = [
    "PASSWORD_MIN_LENGTH",
    "hash_password",
    "validate_password_policy",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_subject",
    "EmailSender",
    "ConsoleEmailSender",
    "SmtpEmailSender",
    "build_message",
    "get_email_sender",
]
