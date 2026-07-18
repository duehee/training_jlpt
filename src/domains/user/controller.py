"""사용자(user) 인증 API (세션 9) — 회원가입.

path·prefix는 controller가 소유(도메인 자율). main은 등록만.
로직은 service에 위임하고, controller는 요청 처리 + 도메인 예외 → HTTP 매핑만 한다.
"""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.session import get_session
from src.domains.session.service import (
    promote_anonymous_session,
    resolve_anonymous_session,
)
from src.shared.auth.oauth import (
    GoogleOAuthClient,
    build_google_authorize_url,
    get_google_oauth_client,
)
from src.shared.auth.tokens import generate_token
from src.web.session import (
    ACCESS_COOKIE_NAME,
    COOKIE_NAME,
    OAUTH_STATE_COOKIE_NAME,
    OAUTH_STATE_MAX_AGE,
)
from src.domains.user.dto.request import (
    LoginRequest,
    ResendVerificationRequest,
    SignupRequest,
)
from src.domains.user.dto.response import (
    LoginResponse,
    ResendVerificationResponse,
    SignupResponse,
    VerifyEmailResponse,
)
from src.domains.user.service import (
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidVerificationTokenError,
    PasswordPolicyError,
    VerificationTokenExpiredError,
    authenticate_user,
    issue_email_verification_token,
    oauth_upsert_user,
    register_user,
    reissue_email_verification_token,
    verify_email_token,
)
from src.shared.auth.email import EmailSender, get_email_sender
from src.shared.auth.jwt import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _verification_email_body(nickname: str, verify_url: str) -> str:
    """확인 메일 본문(plain text). 링크 클릭 시 이메일이 확인된다."""
    return (
        f"{nickname}님, JLPT 진단 서비스 가입을 환영합니다.\n\n"
        f"아래 링크를 눌러 이메일을 확인해 주세요 (24시간 내 유효):\n"
        f"{verify_url}\n\n"
        f"본인이 요청하지 않았다면 이 메일을 무시하셔도 됩니다."
    )


async def _send_verification_email(
    sender: EmailSender, *, email: str, nickname: str, raw_token: str
) -> None:
    """확인 링크 메일 발송. 발송 실패가 가입 자체를 막지 않도록 예외를 흡수한다
    (사용자는 재발송으로 복구 가능 — happy path 강제 X)."""
    # 메일 링크는 SSR 화면(하린 /verify-email)으로 — 클릭 시 결과 화면이 뜬다.
    # (API /api/v1/auth/verify는 회귀 테스트·프로그래매틱 진입점으로 유지.)
    verify_url = f"{settings.app_base_url}/verify-email?token={raw_token}"
    try:
        await sender.send(
            to=email,
            subject="[JLPT] 이메일 확인을 완료해 주세요",
            body=_verification_email_body(nickname, verify_url),
        )
    except Exception:  # noqa: BLE001 — 발송 실패는 로깅만, 가입은 성공 유지
        logger.exception("확인 메일 발송 실패: email=%s", email)


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    body: SignupRequest,
    session: AsyncSession = Depends(get_session),
    sender: EmailSender = Depends(get_email_sender),
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> SignupResponse:
    """이메일/비밀번호 회원가입. 성공 시 미인증 사용자 생성 + 확인 메일 발송.

    게스트 진단 쿠키(session_id)가 있으면 익명 세션의 진단 이력을 새 계정에 승격한다.
    """
    try:
        user = await register_user(
            session,
            email=body.email,
            password=body.password,
            nickname=body.nickname,
        )
    except PasswordPolicyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="이미 가입된 이메일입니다.",
        ) from exc
    raw_token = await issue_email_verification_token(session, user)
    await _send_verification_email(
        sender, email=user.email, nickname=user.nickname, raw_token=raw_token
    )
    if session_token:  # 게스트 진단 이력 승격(익명 세션이 유효할 때만).
        anon = await resolve_anonymous_session(session, session_token)
        if anon is not None:
            await promote_anonymous_session(session, anon, user)
    return SignupResponse.model_validate(user)


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    """이메일/비밀번호 로그인. 성공 시 JWT access token 발급."""
    try:
        user = await authenticate_user(
            session, email=body.email, password=body.password
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        ) from exc
    except EmailNotVerifiedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이메일 확인이 필요합니다. 메일함의 확인 링크를 눌러 주세요.",
        ) from exc
    token = create_access_token(subject=str(user.id))
    return LoginResponse(access_token=token)


@router.get("/verify", response_model=VerifyEmailResponse)
async def verify_email(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> VerifyEmailResponse:
    """확인 링크(GET, 쿼리 token) 처리. 성공 시 이메일 확인 완료."""
    try:
        user = await verify_email_token(session, token)
    except VerificationTokenExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="확인 링크가 만료되었습니다. 확인 메일을 재발송해 주세요.",
        ) from exc
    except InvalidVerificationTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 확인 링크입니다.",
        ) from exc
    return VerifyEmailResponse(email=user.email)


@router.post("/verify/resend", response_model=ResendVerificationResponse)
async def resend_verification(
    body: ResendVerificationRequest,
    session: AsyncSession = Depends(get_session),
    sender: EmailSender = Depends(get_email_sender),
) -> ResendVerificationResponse:
    """확인 메일 재발송. 계정 존재/확인 여부와 무관하게 항상 동일 응답(비노출)."""
    result = await reissue_email_verification_token(session, body.email)
    if result is not None:  # 미확인 사용자일 때만 실제 발송.
        user, raw_token = result
        await _send_verification_email(
            sender, email=user.email, nickname=user.nickname, raw_token=raw_token
        )
    return ResendVerificationResponse()


# ── Google OAuth (세션 9 §a) ──
@router.get("/google")
async def google_authorize() -> RedirectResponse:
    """Google 동의 화면으로 리다이렉트. CSRF 방지용 state를 쿠키에 심는다."""
    state = generate_token()
    response = RedirectResponse(build_google_authorize_url(state))
    response.set_cookie(
        OAUTH_STATE_COOKIE_NAME,
        state,
        max_age=OAUTH_STATE_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_session),
    oauth_client: GoogleOAuthClient = Depends(get_google_oauth_client),
    state_cookie: str | None = Cookie(default=None, alias=OAUTH_STATE_COOKIE_NAME),
) -> RedirectResponse:
    """Google 콜백. state 대조(CSRF) → code 교환 → 계정 upsert → JWT 쿠키 + 리다이렉트."""
    if not state_cookie or state_cookie != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth state 불일치 (요청 위조 의심).",
        )
    try:
        google_user = await oauth_client.exchange_code(code)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google 인증에 실패했습니다.",
        ) from exc

    user = await oauth_upsert_user(
        session,
        provider="google",
        provider_account_id=google_user.sub,
        email=google_user.email,
        name=google_user.name,
    )
    token = create_access_token(subject=str(user.id))
    response = RedirectResponse("/mypage", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        token,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(OAUTH_STATE_COOKIE_NAME)  # 1회용 state 정리
    return response
