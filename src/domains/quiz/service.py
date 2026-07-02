"""진단(quiz) 서비스 — DB 접근 + 흐름 오케스트레이션 (async).

순수 계산(채점/레벨/약점)은 util.py. 여기서는 DB 조회·기록과 결과 집계 흐름.

보안 (api_endpoints §6-2): 출제 문항은 정답(correct_choice)을 포함하지 않는다.
채점은 서버에서만 (`correct_choice`는 절대 직렬화하지 않음).
"""

from __future__ import annotations

import uuid
from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import DiagnosticAnswer, DiagnosticQuestion, DiagnosticSession
from src.domains.quiz.dto.response import ClientQuestion, WeakGrammarPoint
from src.domains.quiz.util import GradedAnswer, aggregate_score, diagnose_level


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


async def compute_result(
        session: AsyncSession, diag: DiagnosticSession
) -> tuple[str | None, int, list[WeakGrammarPoint], str | None]:
    """세션의 답안을 집계 → (레벨, 점수, 약점 목록, 추천 시작점).

    complete/result 공통 흐름. 순수 계산(diagnose_level·aggregate_score)은 util 위임,
    여기서는 DB 조회 + 약점 집계 조립만 담당.
    """
    rows = list(
        (
            await session.execute(
                select(DiagnosticAnswer).where(
                    DiagnosticAnswer.diagnostic_session_id == diag.id
                )
            )
        ).scalars()
    )
    level_rows = (
        await session.execute(
            select(DiagnosticQuestion.question_key, DiagnosticQuestion.level)
        )
    ).all()
    levels: dict[str, str] = {str(k): str(v) for k, v in level_rows}
    graded = [
        GradedAnswer(
            question_key=a.question_id,
            grammar_point_id=a.grammar_point_id,
            level=str(levels.get(a.question_id, "")),
            selected_choice=a.selected_choice,
            correct_choice=a.correct_choice,
            is_correct=a.is_correct,
        )
        for a in rows
    ]
    level = diagnose_level(graded)
    score, _ = aggregate_score(graded)

    # 약점: 오답 grammar_point_id (중복 제거·입력 순서 보존) + error_count·level.
    err_count = Counter(g.grammar_point_id for g in graded if not g.is_correct)
    gp_level = {g.grammar_point_id: g.level for g in graded}
    seen: set[str] = set()
    weak: list[WeakGrammarPoint] = []
    for g in graded:
        if not g.is_correct and g.grammar_point_id not in seen:
            seen.add(g.grammar_point_id)
            weak.append(
                WeakGrammarPoint(
                    grammar_point_id=g.grammar_point_id,
                    error_count=err_count[g.grammar_point_id],
                    level=gp_level[g.grammar_point_id],
                )
            )
    recommended = weak[0].grammar_point_id if weak else None
    return level, score, weak, recommended


async def get_selected_choice(
    session: AsyncSession,
    *,
    diagnostic_session_id: uuid.UUID,
    question_key: str,
) -> str | None:
    """세션이 특정 문항에 이전에 제출한 선택지 key. 없으면 None.

    재방문 시 화면의 이전 선택 복원용(web). 답안 조회(ORM)는 도메인에 둔다.
    """
    answer = (
        await session.execute(
            select(DiagnosticAnswer).where(
                DiagnosticAnswer.diagnostic_session_id == diagnostic_session_id,
                DiagnosticAnswer.question_id == question_key,
            )
        )
    ).scalar_one_or_none()
    return answer.selected_choice if answer is not None else None
