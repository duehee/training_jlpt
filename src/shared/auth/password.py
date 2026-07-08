"""비밀번호 해싱 + 정책 검증 (인증 인프라, 세션 9 Q2=bcrypt).

- 해시: bcrypt(자동 salt). 평문은 저장하지 않고 해시만 users.password_hash에 보관.
- 정책(정빈님 §c lock): 8자 이상 + 영문 + 숫자.

도메인-무관 순수 함수라 shared/auth에 둔다(특정 도메인 서비스에 묶지 않음).
"""

from __future__ import annotations

import re

import bcrypt

# 비밀번호 정책 상수 (정빈님 §c). 매직넘버 방지 위해 상수화.
PASSWORD_MIN_LENGTH = 8

# bcrypt는 입력 72바이트 초과분을 조용히 버린다 → 초과 입력은 정책 위반으로 사전 차단.
_BCRYPT_MAX_BYTES = 72

_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


def validate_password_policy(password: str) -> str | None:
    """정책 위반 사유(한국어)를 반환. 통과하면 None.

    호출측(회원가입 DTO/서비스)이 이 반환값으로 400 응답 메시지를 만든다.
    bool이 아닌 사유 문자열을 돌려주는 이유 = 어떤 규칙을 어겼는지 사용자에게 안내하기 위함.
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return f"비밀번호는 {PASSWORD_MIN_LENGTH}자 이상이어야 합니다."
    if len(password.encode("utf-8")) > _BCRYPT_MAX_BYTES:
        return f"비밀번호는 {_BCRYPT_MAX_BYTES}바이트를 넘을 수 없습니다."
    if not _HAS_LETTER.search(password):
        return "비밀번호는 영문을 포함해야 합니다."
    if not _HAS_DIGIT.search(password):
        return "비밀번호는 숫자를 포함해야 합니다."
    return None


def hash_password(password: str) -> str:
    """평문 비밀번호 → bcrypt 해시 문자열(저장용).

    매 호출 새 salt 생성 → 같은 비밀번호도 매번 다른 해시가 나온다(rainbow table 방어).
    """
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """평문이 저장된 해시와 일치하는지 검증.

    bcrypt.checkpw가 상수시간 비교로 타이밍 공격을 완화한다.
    저장된 해시가 손상돼 파싱 불가하면(ValueError) 일치 실패로 처리.
    """
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except ValueError:
        return False
