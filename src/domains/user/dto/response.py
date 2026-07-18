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


class DashboardData(BaseModel):
    """마이페이지(dashboard) 표시 데이터. 초기 진단 1건 실데이터(세션 9 ④).

    has_diagnostic=False면 진단 이력 없음(화면은 진단 유도 CTA). 약점 보관함/이력
    목록은 데이터 모델상 진단 1건뿐이라 화면에서 플레이스홀더 처리(범위 정빈님).
    """

    nickname: str
    has_diagnostic: bool
    diagnosed_level: str | None = None
    score: int | None = None
    max_score: int | None = None
