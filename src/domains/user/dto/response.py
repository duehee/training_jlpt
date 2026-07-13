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
