"""이메일 표준화(canonicalize) 단위 테스트 (세션 9, 중복 가입 방지).

Gmail 계열: +태그·점 제거 + 도메인 통일 / 그 외 도메인: 소문자화만. DB 불필요.
"""

from __future__ import annotations

import pytest

from src.domains.user.dto.request import (
    LoginRequest,
    SignupRequest,
    canonicalize_email,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("tjwjdqls01+jlpt1@gmail.com", "tjwjdqls01@gmail.com"),  # +태그 제거
        ("tjw.jdqls01@gmail.com", "tjwjdqls01@gmail.com"),  # 점 제거
        ("A.B+work@GoogleMail.com", "ab@gmail.com"),  # 점+태그+도메인 통일
        ("  User@Gmail.com  ", "user@gmail.com"),  # 공백/대문자
        ("user+tag@outlook.com", "user+tag@outlook.com"),  # 비Gmail: local 보존
        ("User@Example.COM", "user@example.com"),  # 비Gmail: 소문자화만
        ("not-an-email", "not-an-email"),  # @ 없음 → 그대로(형식검증은 별도)
    ],
)
def test_canonicalize_email(raw: str, expected: str) -> None:
    assert canonicalize_email(raw) == expected


def test_signup_stores_canonical_gmail() -> None:
    """가입 DTO는 Gmail 별칭을 표준형으로 접어 중복 판정 키를 통일한다."""
    req = SignupRequest(
        email="tjwjdqls01+jlpt1@gmail.com", password="abcd1234", nickname="정빈"
    )
    assert req.email == "tjwjdqls01@gmail.com"


def test_login_uses_same_canonical() -> None:
    """로그인도 같은 규칙으로 접어야 저장값과 매칭된다."""
    req = LoginRequest(email="TJW.jdqls01+x@googlemail.com", password="abcd1234")
    assert req.email == "tjwjdqls01@gmail.com"
