"""사용자(user) 서비스 — 인증 비즈니스 로직 (async, ORM).

회원가입: 비밀번호 정책 검증 → 이메일 중복 확인 → bcrypt 해싱 → users 저장.
발생 가능한 도메인 오류는 예외로 올리고, HTTP 매핑은 controller가 담당한다.
확인 메일 발송(§b)은 S5에서 이 위에 얹는다 — 본 단위는 계정 생성까지.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.models import (
    DiagnosticSession,
    EmailVerificationToken,
    OAuthAccount,
    User,
)
from src.domains.user.dto.response import DashboardData
from src.shared.auth.jwt import get_subject
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


class EmailNotVerifiedError(Exception):
    """이메일 미확인 계정 로그인 시도(정빈님 결정 B). controller가 403으로 매핑.

    자격증명 검증을 통과한 뒤에만 발생 → 계정 존재/비번 노출 아님(정당한 안내).
    """


class InvalidVerificationTokenError(Exception):
    """확인 토큰이 없음/이미 사용됨. controller가 400으로 매핑."""


class VerificationTokenExpiredError(Exception):
    """확인 토큰 만료(TTL 경과). controller가 410으로 매핑 → 재발송 유도."""


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
    # 비번 통과 후 게이팅 — 미확인 계정 차단(정빈님 결정 B).
    # 순서 중요: 비번 검증을 먼저 해야 '틀린 비번'이 계정 상태를 노출하지 않는다.
    if not user.email_verified:
        raise EmailNotVerifiedError()
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


async def verify_email_token(session: AsyncSession, raw_token: str) -> User:
    """확인 링크의 raw 토큰을 검증하고 해당 사용자를 email_verified=True로 전환.

    토큰 재사용(consumed) 방지 + 만료 확인. 성공 시 토큰을 소비 처리한다.
    조회는 raw가 아니라 해시로 한다(DB엔 해시만 저장돼 있으므로).
    """
    token_hash = hash_token(raw_token)
    token = (
        await session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash
            )
        )
    ).scalar_one_or_none()
    if token is None or token.consumed_at is not None:
        raise InvalidVerificationTokenError()
    if token.expires_at <= datetime.now(timezone.utc):
        raise VerificationTokenExpiredError()

    user = (
        await session.execute(select(User).where(User.id == token.user_id))
    ).scalar_one_or_none()
    if user is None:  # CASCADE로 보통 함께 지워지나 방어적으로 확인.
        raise InvalidVerificationTokenError()

    user.email_verified = True
    token.consumed_at = datetime.now(timezone.utc)
    await session.commit()
    return user


async def reissue_email_verification_token(
    session: AsyncSession, email: str
) -> tuple[User, str] | None:
    """미확인 사용자에게 새 확인 토큰 발급 후 (user, raw) 반환.

    사용자 미존재 또는 이미 확인됨 → None(호출측은 발송 생략, 응답은 항상 동일).
    재발송 시 기존 미소비 토큰을 무효화(consumed 처리)해 옛 링크를 폐기한다.
    """
    user = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if user is None or user.email_verified:
        return None

    now = datetime.now(timezone.utc)
    existing = (
        await session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.consumed_at.is_(None),
            )
        )
    ).scalars().all()
    for old in existing:
        old.consumed_at = now  # 옛 링크 무효화 — 최신 링크만 유효

    raw_token = generate_token()
    session.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=now
            + timedelta(hours=settings.email_verification_ttl_hours),
        )
    )
    await session.commit()
    return user, raw_token


async def get_user_by_id(
    session: AsyncSession, user_id: uuid.UUID
) -> User | None:
    """id로 사용자 조회. 없으면 None."""
    return (
        await session.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()


async def resolve_user_from_token(
    session: AsyncSession, token: str
) -> User | None:
    """JWT access token → User. 무효/만료/파싱실패/미존재는 모두 None.

    web(SSR)이 쿠키에서 꺼낸 토큰을 넘기면 로그인 사용자를 돌려준다(쿠키 읽기는 web 담당).
    """
    subject = get_subject(token)
    if subject is None:
        return None
    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        return None
    return await get_user_by_id(session, user_id)


async def get_user_dashboard(
    session: AsyncSession, user: User
) -> DashboardData:
    """마이페이지 표시 데이터. 승격된 초기 진단 1건의 저장 결과를 읽어 반환(④).

    진단 완료 이력이 없으면 has_diagnostic=False(화면은 진단 유도). 저장된
    diagnosed_level/score를 그대로 읽어 quiz 재계산·교차 도메인 결합을 피한다.
    """
    if user.initial_diagnostic_session_id is None:
        return DashboardData(nickname=user.nickname, has_diagnostic=False)
    diag = (
        await session.execute(
            select(DiagnosticSession).where(
                DiagnosticSession.id == user.initial_diagnostic_session_id
            )
        )
    ).scalar_one_or_none()
    if diag is None or diag.status != "completed":
        return DashboardData(nickname=user.nickname, has_diagnostic=False)
    return DashboardData(
        nickname=user.nickname,
        has_diagnostic=True,
        diagnosed_level=diag.diagnosed_level,
        score=diag.score,
        max_score=diag.max_score,
    )


async def oauth_upsert_user(
    session: AsyncSession,
    *,
    provider: str,
    provider_account_id: str,
    email: str,
    name: str | None = None,
) -> User:
    """OAuth 로그인/가입. 기존 연결 계정이면 그 user 반환, 없으면 연결·생성.

    - 이미 (provider, account_id)로 연결된 계정 → 로그인
    - 미연결 + 같은 email의 기존 user 존재 → 그 user에 OAuth 계정 연결(계정 통합)
    - 둘 다 아니면 신규 user 생성(비밀번호 없음, email_verified=True — provider가 검증)
    """
    account = (
        await session.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_account_id == provider_account_id,
            )
        )
    ).scalar_one_or_none()
    if account is not None:
        return (
            await session.execute(select(User).where(User.id == account.user_id))
        ).scalar_one()

    user = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            nickname=(name or email.split("@")[0])[:50],
            password_hash=None,  # 소셜 전용 — 비밀번호 로그인 불가
            email_verified=True,  # provider가 이메일 소유를 검증함
        )
        session.add(user)
        await session.flush()  # user.id 확보(OAuth 계정 FK용)

    session.add(
        OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_account_id=provider_account_id,
            email=email,
        )
    )
    await session.commit()
    await session.refresh(user)
    return user
