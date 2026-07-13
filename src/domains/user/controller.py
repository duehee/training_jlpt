"""사용자(user) 인증 API (세션 9) — 회원가입.

path·prefix는 controller가 소유(도메인 자율). main은 등록만.
로직은 service에 위임하고, controller는 요청 처리 + 도메인 예외 → HTTP 매핑만 한다.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.session import get_session
from src.domains.user.dto.request import LoginRequest, SignupRequest
from src.domains.user.dto.response import LoginResponse, SignupResponse
from src.domains.user.service import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    PasswordPolicyError,
    authenticate_user,
    issue_email_verification_token,
    register_user,
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
    verify_url = f"{settings.app_base_url}/api/v1/auth/verify?token={raw_token}"
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
) -> SignupResponse:
    """이메일/비밀번호 회원가입. 성공 시 미인증 사용자 생성 + 확인 메일 발송."""
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
    token = create_access_token(subject=str(user.id))
    return LoginResponse(access_token=token)
