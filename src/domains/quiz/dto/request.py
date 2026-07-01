"""진단(quiz) 요청 DTO — 클라이언트 → 서버 (api_endpoints §6).

요청 계약만 담는다. 응답은 response.py, 비즈니스 로직은 service.py 참조.
"""

from __future__ import annotations

from pydantic import BaseModel


# ── §6-1 진단 세션 시작 ──
class StartDiagnosticRequest(BaseModel):
    mode: str = "initial_assessment"


# ── §6-3 답안 제출 ──
class SubmitAnswerRequest(BaseModel):
    question_id: str
    selected_choice: str
    time_spent_sec: int | None = None
