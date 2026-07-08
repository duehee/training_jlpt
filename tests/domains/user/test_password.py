"""비밀번호 해싱 + 정책 검증 단위 테스트 (세션 9 S3-①).

DB 불필요 — 순수 함수. bcrypt roundtrip / 정책(8자+영문+숫자) / 손상 해시 방어.
"""

from __future__ import annotations

from src.shared.auth.password import (
    hash_password,
    validate_password_policy,
    verify_password,
)


def test_hash_verify_roundtrip() -> None:
    """정상 비밀번호는 해시 후 검증에 성공한다."""
    plain = "abcd1234"
    hashed = hash_password(plain)
    assert hashed != plain  # 평문 저장 금지
    assert verify_password(plain, hashed) is True


def test_wrong_password_rejected() -> None:
    hashed = hash_password("abcd1234")
    assert verify_password("wrong9999", hashed) is False


def test_salt_makes_hashes_unique() -> None:
    """같은 비밀번호라도 salt 때문에 매번 다른 해시가 나온다."""
    h1 = hash_password("abcd1234")
    h2 = hash_password("abcd1234")
    assert h1 != h2
    assert verify_password("abcd1234", h1)
    assert verify_password("abcd1234", h2)


def test_policy_accepts_valid() -> None:
    assert validate_password_policy("abcd1234") is None


def test_policy_rejects_too_short() -> None:
    msg = validate_password_policy("ab12")
    assert msg is not None and "8자" in msg


def test_policy_rejects_no_letter() -> None:
    msg = validate_password_policy("12345678")
    assert msg is not None and "영문" in msg


def test_policy_rejects_no_digit() -> None:
    msg = validate_password_policy("abcdefgh")
    assert msg is not None and "숫자" in msg


def test_policy_rejects_over_72_bytes() -> None:
    """bcrypt 72바이트 한도 초과는 정책에서 사전 차단(조용한 절삭 방지)."""
    msg = validate_password_policy("a1" + "가" * 30)  # 2 + 90바이트
    assert msg is not None and "72" in msg


def test_verify_handles_corrupt_hash() -> None:
    """저장 해시가 손상돼도 예외 없이 실패로 처리한다."""
    assert verify_password("abcd1234", "not-a-valid-bcrypt-hash") is False
