"""일회성 토큰 생성 + 해시 (인증 인프라, 세션 9 §b).

이메일 확인 토큰 등에 사용. raw 토큰은 링크로만 전달하고, DB엔 sha256 해시만 저장한다
(유출 대비 — 저장된 해시로는 raw를 역산할 수 없다).
"""

from __future__ import annotations

import hashlib
import secrets


def generate_token() -> str:
    """URL-safe 랜덤 raw 토큰. 링크에 실려 사용자에게 전달된다."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """raw 토큰 → sha256 hex(64자). DB 저장·조회 키로 사용.

    비밀번호와 달리 salt/bcrypt가 아닌 단순 sha256인 이유 = 토큰 자체가 이미
    고엔트로피 랜덤(추측 불가)이라 rainbow table 위협이 없고, 조회 시 O(1) 매칭이 필요.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
