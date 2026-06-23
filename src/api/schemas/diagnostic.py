"""진단/세션 API 요청·응답 모델 (api_endpoints §5·§6).

출제 응답은 `ClientQuestion`(정답 제외, 정빈님 flow 불변식)을 그대로 재사용한다.
explanation 프리뷰(§8-3 게스트 경로)는 `03_api_consumer_contract_draft.md` 3블록 구조.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.services.diagnostic.flow import ClientQuestion

# 본 사이클 진단 출제 레벨 (N5 적재 + N4 진단 문항). 셔플 없음(결정적, 정빈님 D-셔플).
DIAGNOSTIC_LEVELS: tuple[str, ...] = ("N5", "N4")


# ── §5-1 익명 세션 ──
class AnonymousSessionResponse(BaseModel):
    session_token: str
    expires_at: datetime


# ── §6-1 진단 세션 시작 ──
class StartDiagnosticRequest(BaseModel):
    mode: str = "initial_assessment"


class StartDiagnosticResponse(BaseModel):
    diagnostic_session_id: str
    status: str
    max_score: int
    started_at: datetime


# ── §6-2 출제 ──
class QuestionsResponse(BaseModel):
    diagnostic_session_id: str
    questions: list[ClientQuestion]


# ── §6-3 답안 제출 ──
class SubmitAnswerRequest(BaseModel):
    question_id: str
    selected_choice: str
    time_spent_sec: int | None = None


class AnswerProgress(BaseModel):
    answered: int
    total: int


class SubmitAnswerResponse(BaseModel):
    answer_id: str
    is_correct: bool
    progress: AnswerProgress


# ── §6-4 / §6-5 완료·결과 ──
class WeakGrammarPoint(BaseModel):
    grammar_point_id: str
    error_count: int
    level: str


class DiagnosticResultResponse(BaseModel):
    diagnostic_session_id: str
    diagnosed_level: str | None
    score: int
    max_score: int
    weak_grammar_points: list[WeakGrammarPoint]
    recommended_start_point: str | None
    completed_at: datetime | None


# ── §8-3 explanation 프리뷰 (게스트 경로, 03 §2-3 3블록) ──
class RetrievedBlock(BaseModel):
    """retrieval 원본 청크 (가공 없음, 사실)."""

    point_chunk: dict[str, Any] | None
    compare_chunks: list[dict[str, Any]]


class ExplanationPreviewResponse(BaseModel):
    grammar_point_id: str
    level: str
    retrieved: RetrievedBlock
    generated_explanation: str
    examples: list[str] = Field(default_factory=list)
    cached: bool
