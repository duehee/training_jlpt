"""사용자(user) 인증 API (세션 9) — 회원가입.

path·prefix는 controller가 소유(도메인 자율). main은 등록만.
로직은 service에 위임하고, controller는 요청 처리 + 도메인 예외 → HTTP 매핑만 한다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.domains.user.dto.request import SignupRequest
from src.domains.user.dto.response import SignupResponse
from src.domains.user.service import (
    EmailAlreadyExistsError,
    PasswordPolicyError,
    register_user,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    body: SignupRequest,
    session: AsyncSession = Depends(get_session),
) -> SignupResponse:
    """이메일/비밀번호 회원가입. 성공 시 미인증 사용자 생성."""
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
    return SignupResponse.model_validate(user)
