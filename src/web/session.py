"""쿠키 ↔ 익명 세션 해소 헬퍼 (B FK 패턴).

웹 SSR은 쿠키 `session_id`(= `anonymous_sessions.session_token`)로 익명 세션을
해소하고, `active_diagnostic_session_id`(마이그레이션 0003)로 현재 진단 세션을
1홉으로 가리킨다. 기존 `src/api/routes/sessions.py` 의 토큰/TTL 패턴을 재활용한다.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import AnonymousSession

COOKIE_NAME = "session_id"
COOKIE_MAX_AGE = 24 * 60 * 60  # 24h (익명 세션 TTL과 일치)
_ANON_TTL = timedelta(hours=24)


async def resolve_anon(
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


async def create_anon(session: AsyncSession) -> AnonymousSession:
    """새 익명 세션 생성 + 커밋 (sessions.py 패턴 재활용)."""
    token = f"sess_{secrets.token_urlsafe(24)}"
    expires_at = datetime.now(timezone.utc) + _ANON_TTL
    anon = AnonymousSession(session_token=token, expires_at=expires_at)
    session.add(anon)
    await session.commit()
    await session.refresh(anon)
    return anon


async def clear_active_diag(session: AsyncSession, anon: AnonymousSession) -> None:
    """활성 진단 포인터 해제(`/restart`). 기존 진단 세션 행은 보존, 포인터만 NULL."""
    anon.active_diagnostic_session_id = None
    await session.commit()
