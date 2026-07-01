"""진단(quiz) 응답 DTO — 서버 → 클라이언트 (api_endpoints §6).

응답 계약만 담는다 (순수 — 도메인 로직/ORM import 금지, 규칙 2).
출제 응답 `ClientQuestion`은 정답(correct_choice)을 절대 포함하지 않는다(정빈님 flow 불변식).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── §6-2 출제 문항 (정답 제외) ──
class ClientQuestion(BaseModel):
    """클라이언트로 나가는 문항 (정답 제외).

    학습자 가독성 보강(정빈님 verify): prompt_furigana(ruby HTML) / prompt_ko(한국어).
    choices 항목은 {"key","text"} + 선택적 "text_ko" — correct_choice는 절대 미포함.
    """

    question_id: str  # question_key
    grammar_point_id: str
    level: str
    prompt: str
    prompt_furigana: str | None = None
    prompt_ko: str | None = None
    choices: list[dict[str, Any]]


# ── §6-1 진단 세션 시작 ──
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
