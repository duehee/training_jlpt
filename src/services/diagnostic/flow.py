"""진단 흐름 — 출제 직렬화(순수) + DB 래퍼 + 약점 도출.

순수/DB 분리 (학습 루프 services 패턴 계승):
- `to_client_question` / `derive_weak_point_ids` : DB 무관 순수 → 단위 테스트.
- `fetch_questions` / `record_answer` : DB 래퍼 (정식 문항 도착 시 동작).

보안 (api_endpoints §6-2): 클라이언트에 반환하는 문항은 **정답을 포함하지 않는다**.
채점은 서버에서만 (`correct_choice` 컬럼은 절대 직렬화하지 않음).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import DiagnosticAnswer, DiagnosticQuestion
from src.services.diagnostic.scoring import GradedAnswer


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


def to_client_question(question: DiagnosticQuestion) -> ClientQuestion:
    """DiagnosticQuestion → 클라 직렬화. correct_choice 는 의도적으로 제외."""
    choices = question.choices
    # choices 는 [{"key": "A", "text": "...", "text_ko"?: "..."}] 형태(api_endpoints §6-2).
    items = choices if isinstance(choices, list) else choices.get("items", [])
    return ClientQuestion(
        question_id=question.question_key,
        grammar_point_id=question.grammar_point_id,
        level=question.level,
        prompt=question.stem,
        prompt_furigana=question.stem_furigana,
        prompt_ko=question.stem_ko,
        choices=list(items),
    )


def derive_weak_point_ids(answers: list[GradedAnswer]) -> list[str]:
    """오답 문항의 grammar_point_id 목록 (중복 제거, 입력 순서 보존).

    로그인 승계 시 weak_points 생성의 입력 (D-8: base point only).
    """
    seen: set[str] = set()
    result: list[str] = []
    for a in answers:
        if not a.is_correct and a.grammar_point_id not in seen:
            seen.add(a.grammar_point_id)
            result.append(a.grammar_point_id)
    return result


async def fetch_questions(
    session: AsyncSession,
    *,
    levels: list[str],
    limit: int = 10,
) -> list[DiagnosticQuestion]:
    """주어진 레벨들의 진단 문항을 limit개까지 조회 (출제용).

    정식 문항이 `diagnostic_questions`에 적재되면 동작한다. 현재는 0건이라
    빈 리스트를 반환한다 (뼈대 — 수진 정식 문항 도착 대기).
    """
    stmt = (
        select(DiagnosticQuestion)
        .where(DiagnosticQuestion.level.in_(levels))
        .order_by(DiagnosticQuestion.level, DiagnosticQuestion.question_key)
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def record_answer(
    session: AsyncSession,
    *,
    diagnostic_session_id: Any,
    graded: GradedAnswer,
    time_spent_sec: int | None = None,
) -> None:
    """채점된 답안을 diagnostic_answers 에 기록 (UNIQUE: session+question)."""
    session.add(
        DiagnosticAnswer(
            diagnostic_session_id=diagnostic_session_id,
            question_id=graded.question_key,
            grammar_point_id=graded.grammar_point_id,
            selected_choice=graded.selected_choice,
            correct_choice=graded.correct_choice,
            is_correct=graded.is_correct,
            time_spent_sec=time_spent_sec,
        )
    )
    await session.commit()
