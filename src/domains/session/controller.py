"""세션(session) API (api_endpoints §5) — 익명 세션 생성.

path·prefix는 controller가 소유(도메인 자율). main은 등록만.
생성 로직은 service에 위임하고, controller는 요청 처리 + 응답 포장만 한다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.domains.session.dto.response import AnonymousSessionResponse
from src.domains.session.service import create_anonymous_session as create_session

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post(
    "/anonymous",
    response_model=AnonymousSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_anonymous_session(
    session: AsyncSession = Depends(get_session),
) -> AnonymousSessionResponse:
    """익명 세션을 생성하고 토큰을 반환한다."""
    anon = await create_session(session)
    return AnonymousSessionResponse(
        session_token=anon.session_token, expires_at=anon.expires_at
    )
