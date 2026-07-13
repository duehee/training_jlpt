"""사용자(user) 서비스 — 인증 비즈니스 로직 (async, ORM).

회원가입: 비밀번호 정책 검증 → 이메일 중복 확인 → bcrypt 해싱 → users 저장.
발생 가능한 도메인 오류는 예외로 올리고, HTTP 매핑은 controller가 담당한다.
확인 메일 발송(§b)은 S5에서 이 위에 얹는다 — 본 단위는 계정 생성까지.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.models import EmailVerificationToken, User
from src.shared.auth.password import (
    hash_password,
    validate_password_policy,
    verify_password,
)
from src.shared.auth.tokens import generate_token, hash_token


class PasswordPolicyError(Exception):
    """비밀번호가 정책(8자+영문+숫자)을 위반. 메시지는 사용자 안내용(한국어)."""


class EmailAlreadyExistsError(Exception):
    """이미 가입된 이메일. controller가 409로 매핑."""


class InvalidCredentialsError(Exception):
    """이메일 미존재 또는 비밀번호 불일치. controller가 401로 매핑.

    두 경우를 구분하지 않는다 — "이메일이 없음"과 "비번 틀림"을 다르게 응답하면
    공격자가 가입된 이메일 목록을 캐낼 수 있다(user enumeration). 항상 같은 401.
    """


async def register_user(
    session: AsyncSession, *, email: str, password: str, nickname: str
) -> User:
    """신규 사용자 생성 후 반환. email_verified=False(확인 전).

    email은 DTO에서 이미 정규화(소문자)된 값이 온다고 가정한다.
    """
    policy_error = validate_password_policy(password)
    if policy_error is not None:
        raise PasswordPolicyError(policy_error)

    # 사전 중복 확인 — 대부분의 중복을 친절한 메시지로 조기 차단.
    existing = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing is not None:
        raise EmailAlreadyExistsError(email)

    user = User(
        email=email,
        nickname=nickname,
        password_hash=hash_password(password),
        email_verified=False,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        # 동시 가입 경합 — 사전 확인을 통과한 두 요청이 같은 이메일로 커밋 시도.
        await session.rollback()
        raise EmailAlreadyExistsError(email) from exc
    await session.refresh(user)
    return user


async def authenticate_user(
    session: AsyncSession, *, email: str, password: str
) -> User:
    """이메일+비밀번호 검증 후 User 반환. 실패 시 InvalidCredentialsError.

    email은 DTO에서 정규화(소문자)된 값이 온다고 가정한다.
    password_hash가 None인 계정(OAuth 전용 가입자)은 비밀번호 로그인 불가.
    """
    user = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    # 미존재·OAuth전용·비번불일치를 모두 같은 예외로 → 계정 존재 여부 비노출.
    if user is None or user.password_hash is None:
        raise InvalidCredentialsError()
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    return user


async def issue_email_verification_token(
    session: AsyncSession, user: User
) -> str:
    """확인 토큰 발급 후 raw 토큰 반환(메일 링크용). DB엔 해시만 저장.

    TTL은 settings.email_verification_ttl_hours(Q6=24h). 반환된 raw는 저장되지 않으니
    호출측이 즉시 메일에 실어 보내야 한다.
    """
    raw_token = generate_token()
    token = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=settings.email_verification_ttl_hours),
    )
    session.add(token)
    await session.commit()
    return raw_token
