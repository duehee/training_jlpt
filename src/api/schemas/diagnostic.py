"""세션 API 요청·응답 모델 (api_endpoints §5).

진단(quiz) DTO는 `domains/quiz/dto/{request,response}.py`로 이관됨 (세션 8 Step 3a).
잔존: 익명 세션 응답(§5-1) + 진단 출제 레벨 상수.
- `AnonymousSessionResponse`는 session 도메인 이관 예정 (Step 4).
- `DIAGNOSTIC_LEVELS`는 quiz util로 이관됨 (Step 3b 완료).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

# ── §5-1 익명 세션 ──
class AnonymousSessionResponse(BaseModel):
    session_token: str
    expires_at: datetime
