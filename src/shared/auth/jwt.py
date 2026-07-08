"""JWT access token 발급/검증 (인증 인프라, 세션 9 Q1=B).

로그인 성공 시 user id를 담은 서명 토큰을 발급하고, 이후 요청에서 이 토큰을
검증해 "누구인지"를 확인한다. 서버는 상태를 들고 있지 않는다(stateless).

- 서명: HS256(대칭키). 키는 settings.jwt_secret_key (프로덕션은 .env override 필수).
- 만료: settings.jwt_access_token_expire_minutes(기본 24h). exp 클레임에 실린다.
- refresh token은 본 세션 범위 밖(MVP는 단일 access token).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from src.core.config import settings


def create_access_token(
    subject: str, expires_minutes: int | None = None
) -> str:
    """subject(보통 user id)를 담은 서명 access token 문자열 반환.

    exp(만료)를 항상 포함한다 → 탈취된 토큰도 시간이 지나면 무효.
    expires_minutes 미지정 시 settings 기본값 사용.
    """
    minutes = (
        expires_minutes
        if expires_minutes is not None
        else settings.jwt_access_token_expire_minutes
    )
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    claims: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(
        claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> dict[str, Any] | None:
    """토큰 검증 후 payload 반환. 서명 불일치·만료·손상이면 None.

    None을 돌려주는 이유 = 인증 의존성에서 "유효하지 않은 토큰 → 401"로 다루기 쉽게.
    만료와 위조를 구분하지 않는다(호출측은 둘 다 "재로그인 필요"로 처리).
    """
    try:
        return jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return None


def get_subject(token: str) -> str | None:
    """유효 토큰에서 subject(user id)만 꺼낸다. 무효거나 sub 없으면 None."""
    payload = decode_access_token(token)
    if payload is None:
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None
