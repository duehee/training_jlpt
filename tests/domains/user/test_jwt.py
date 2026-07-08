"""JWT access token 발급/검증 단위 테스트 (세션 9 S3-②).

roundtrip / subject 추출 / 만료 / 위조(서명 불일치) / 손상 토큰 방어.
"""

from __future__ import annotations

from src.shared.auth.jwt import (
    create_access_token,
    decode_access_token,
    get_subject,
)


def test_roundtrip_subject() -> None:
    """발급한 토큰을 디코드하면 subject가 복원된다."""
    token = create_access_token("user-123")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert "exp" in payload  # 만료 클레임 항상 포함


def test_get_subject_helper() -> None:
    token = create_access_token("user-abc")
    assert get_subject(token) == "user-abc"


def test_expired_token_rejected() -> None:
    """만료(음수 수명) 토큰은 None으로 거부된다."""
    token = create_access_token("user-123", expires_minutes=-1)
    assert decode_access_token(token) is None
    assert get_subject(token) is None


def test_tampered_token_rejected() -> None:
    """페이로드를 변조하면 서명 불일치로 거부된다."""
    token = create_access_token("user-123")
    # 마지막 문자를 바꿔 서명을 깨뜨린다.
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    assert decode_access_token(tampered) is None


def test_garbage_token_rejected() -> None:
    """JWT 형식이 아닌 문자열도 예외 없이 None."""
    assert decode_access_token("not.a.jwt") is None
    assert get_subject("") is None
