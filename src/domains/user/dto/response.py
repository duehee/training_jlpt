"""사용자(user) 응답 DTO — 서버 → 클라이언트 (세션 9 인증).

순수 계약. 민감정보(password_hash) 비노출 — 응답에 담을 필드만 명시한다.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class SignupResponse(BaseModel):
    """회원가입 결과. ORM User에서 직접 매핑(from_attributes)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    nickname: str
    email_verified: bool


class LoginResponse(BaseModel):
    """로그인 결과. JWT access token 발급(Bearer 스킴)."""

    access_token: str
    token_type: str = "bearer"


class VerifyEmailResponse(BaseModel):
    """이메일 확인 결과."""

    status: str = "verified"
    email: str


class ResendVerificationResponse(BaseModel):
    """확인 메일 재발송 결과. 계정 존재 여부와 무관하게 항상 동일 메시지."""

    message: str = "해당 계정이 확인 대기 중이라면 확인 메일을 재발송했습니다."
