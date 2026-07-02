"""세션(session) 응답 DTO — 서버 → 클라이언트 (api_endpoints §5).

익명 세션 생성 응답. 순수 계약 (도메인 로직/ORM import 금지, 규칙 2).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


# ── §5-1 익명 세션 ──
class AnonymousSessionResponse(BaseModel):
    session_token: str
    expires_at: datetime
