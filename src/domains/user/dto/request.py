"""사용자(user) 요청 DTO — 클라이언트 → 서버 (세션 9 인증).

요청 계약만 담는다. 응답은 response.py, 비즈니스 로직은 service.py 참조.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

# 가벼운 형식 검증 — "정상 모양"만 거른다. 실질 유효성은 SMTP 확인 메일이 담당.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Gmail 계열은 +태그·점(.)을 무시해 같은 메일함으로 배달된다 → 중복 가입 방지 위해
# 표준형(canonical)으로 접는다. 다른 도메인은 부작용 방지 위해 소문자화만.
_GMAIL_DOMAINS = {"gmail.com", "googlemail.com"}


def canonicalize_email(raw: str) -> str:
    """이메일을 계정 식별용 표준형으로 정규화.

    - 공통: 앞뒤 공백 제거 + 소문자화.
    - Gmail/googlemail: local part의 '+태그' 제거 + '.' 제거 + 도메인 gmail.com 통일.
      (a.b+work@googlemail.com → ab@gmail.com) — 같은 사람의 중복 가입을 막는다.
    - 그 외 도메인: local part는 건드리지 않는다(+가 유효한 별도 주소일 수 있음).
    """
    email = raw.strip().lower()
    local, sep, domain = email.partition("@")
    if not sep:
        return email
    if domain in _GMAIL_DOMAINS:
        local = local.split("+", 1)[0].replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


class SignupRequest(BaseModel):
    """회원가입 요청. 비밀번호 정책 검증은 service(공용 정책 함수)에 위임."""

    email: str
    password: str
    nickname: str = Field(min_length=1, max_length=50)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        """표준형 정규화 후 형식 확인. 중복 가입 방지(Gmail 별칭·점 접기 포함)."""
        normalized = canonicalize_email(value)
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
        # 저장값과 동일 표준형으로 접어야 로그인 매칭이 된다(가입과 같은 규칙).
        return canonicalize_email(value)


class ResendVerificationRequest(BaseModel):
    """확인 메일 재발송 요청. 응답은 항상 동일(계정 존재 비노출)이라 정규화만 한다."""

    email: str

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return canonicalize_email(value)
