"""세션(session) 서비스 — 익명 세션 생명주기 (async, ORM).

쿠키↔세션 해소 + 생성 + 활성 진단 포인터 관리. 쿠키 자체(이름·TTL 헤더)는
HTTP presentation 관심사라 web에 남기고, 여기서는 세션 데이터(ORM)만 다룬다.
기존 web/session.py + 세션 라우트의 중복 토큰 로직을 단일 출처로 통합.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import AnonymousSession, User

# 익명 세션 TTL (진단 한 사이클 보존 — 데모 기본 24h).
_ANON_TTL = timedelta(hours=24)


async def create_anonymous_session(session: AsyncSession) -> AnonymousSession:
    """새 익명 세션 생성 + 커밋. 토큰은 `sess_` prefix + URL-safe 랜덤."""
    token = f"sess_{secrets.token_urlsafe(24)}"
    expires_at = datetime.now(timezone.utc) + _ANON_TTL
    anon = AnonymousSession(session_token=token, expires_at=expires_at)
    session.add(anon)
    await session.commit()
    await session.refresh(anon)
    return anon


async def resolve_anonymous_session(
    session: AsyncSession, token: str | None
) -> AnonymousSession | None:
    """쿠키 토큰 → 유효·미만료 익명 세션. 무효/만료/없음 → None."""
    if not token:
        return None
    anon = (
        await session.execute(
            select(AnonymousSession).where(AnonymousSession.session_token == token)
        )
    ).scalar_one_or_none()
    if anon is None or anon.expires_at <= datetime.now(timezone.utc):
        return None
    return anon


async def clear_active_diagnostic(
    session: AsyncSession, anon: AnonymousSession
) -> None:
    """활성 진단 포인터 해제(`/restart`). 진단 세션 행은 보존, 포인터만 NULL."""
    anon.active_diagnostic_session_id = None
    await session.commit()


async def set_active_diagnostic(
    session: AsyncSession,
    anon: AnonymousSession,
    diagnostic_session_id: uuid.UUID,
) -> None:
    """익명 세션의 활성 진단 포인터 설정 + 커밋(진단 시작 시 web에서 호출)."""
    anon.active_diagnostic_session_id = diagnostic_session_id
    await session.commit()


async def promote_anonymous_session(
    session: AsyncSession, anon: AnonymousSession, user: User
) -> bool:
    """게스트 익명 세션을 신규 user에 승격(회원가입 시 진단 이력 이전).

    - anon.linked_user_id ← user.id (익명 세션을 계정에 연결)
    - user.initial_diagnostic_session_id ← anon의 진단 세션(최초 진단으로 기록)

    이미 다른 계정에 연결된 익명 세션(linked_user_id != None)은 승격하지 않고 False.
    자기 진단 이력을 자기 새 계정에 잇는 것이라 hijack 위험 없음(본인 쿠키 기준).
    """
    if anon.linked_user_id is not None:
        return False
    anon.linked_user_id = user.id
    if anon.active_diagnostic_session_id is not None:
        user.initial_diagnostic_session_id = anon.active_diagnostic_session_id
    await session.commit()
    return True
