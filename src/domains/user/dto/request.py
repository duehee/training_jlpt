"""사용자(user) 요청 DTO — 클라이언트 → 서버 (세션 9 인증).

요청 계약만 담는다. 응답은 response.py, 비즈니스 로직은 service.py 참조.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

# 가벼운 형식 검증 — "정상 모양"만 거른다. 실질 유효성은 SMTP 확인 메일이 담당.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupRequest(BaseModel):
    """회원가입 요청. 비밀번호 정책 검증은 service(공용 정책 함수)에 위임."""

    email: str
    password: str
    nickname: str = Field(min_length=1, max_length=50)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        """소문자화 + 공백 제거로 정규화 후 형식 확인.

        정규화하는 이유 = 'A@x.com'과 'a@x.com'이 다른 계정으로 중복 가입되는 것 방지.
        """
        normalized = value.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise ValueError("이메일 형식이 올바르지 않습니다.")
        return normalized


class LoginRequest(BaseModel):
    """로그인 요청. 형식 검증(422)은 하지 않는다 — 잘못된 입력도 일괄 401로 처리해
    계정 존재 여부를 노출하지 않기 위함. 저장값 매칭 위해 정규화만 한다."""

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class ResendVerificationRequest(BaseModel):
    """확인 메일 재발송 요청. 응답은 항상 동일(계정 존재 비노출)이라 정규화만 한다."""

    email: str

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()
