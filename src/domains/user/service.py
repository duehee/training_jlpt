"""사용자(user) 서비스 — 인증 비즈니스 로직 (async, ORM).

회원가입: 비밀번호 정책 검증 → 이메일 중복 확인 → bcrypt 해싱 → users 저장.
발생 가능한 도메인 오류는 예외로 올리고, HTTP 매핑은 controller가 담당한다.
확인 메일 발송(§b)은 S5에서 이 위에 얹는다 — 본 단위는 계정 생성까지.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.shared.auth.password import hash_password, validate_password_policy


class PasswordPolicyError(Exception):
    """비밀번호가 정책(8자+영문+숫자)을 위반. 메시지는 사용자 안내용(한국어)."""


class EmailAlreadyExistsError(Exception):
    """이미 가입된 이메일. controller가 409로 매핑."""


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
        # DB unique(uq_users_email)가 최종 방어선 → 진실은 DB.
        await session.rollback()
        raise EmailAlreadyExistsError(email) from exc
    await session.refresh(user)
    return user
