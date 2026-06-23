"""세션 API (api_endpoints §5).

§5-1 익명 세션 생성 — 진단 시작 전 비로그인 사용자의 임시 세션.
인증 불필요. 토큰은 이후 진단 엔드포인트의 `Authorization: Session {token}`에 사용.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.diagnostic import AnonymousSessionResponse
from src.db.models import AnonymousSession
from src.db.session import get_session

router = APIRouter(tags=["sessions"])

# 익명 세션 TTL (진단 한 사이클에 충분한 보존 — 데모 기본 24h).
_ANON_TTL = timedelta(hours=24)


@router.post(
    "/anonymous",
    response_model=AnonymousSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_anonymous_session(
    session: AsyncSession = Depends(get_session),
) -> AnonymousSessionResponse:
    """익명 세션을 생성하고 토큰을 반환한다."""
    token = f"sess_{secrets.token_urlsafe(24)}"
    expires_at = datetime.now(timezone.utc) + _ANON_TTL
    anon = AnonymousSession(session_token=token, expires_at=expires_at)
    session.add(anon)
    await session.commit()
    return AnonymousSessionResponse(session_token=token, expires_at=expires_at)
