"""진단 채점 — 순수 로직 (DB/LLM 무관).

4지선다 진단은 규칙 채점이다 (LLM 미사용). selected == correct 비교만으로
정오를 판정하고 점수를 집계한다. 학습 루프 Stage 2의 이해도 문제 채점과 동일
원리지만, 진단은 '레벨 판정'이 목적이라 별도 도메인으로 둔다.
"""

from __future__ import annotations

from pydantic import BaseModel


class GradedAnswer(BaseModel):
    """한 문항의 채점 결과 (레벨 판정·약점 도출의 입력)."""

    question_key: str
    grammar_point_id: str
    level: str
    selected_choice: str
    correct_choice: str
    is_correct: bool


def grade_answer(
    *,
    question_key: str,
    grammar_point_id: str,
    level: str,
    selected_choice: str,
    correct_choice: str,
) -> GradedAnswer:
    """단일 답안 채점. selected == correct → is_correct."""
    return GradedAnswer(
        question_key=question_key,
        grammar_point_id=grammar_point_id,
        level=level,
        selected_choice=selected_choice,
        correct_choice=correct_choice,
        is_correct=selected_choice == correct_choice,
    )


def aggregate_score(answers: list[GradedAnswer]) -> tuple[int, int]:
    """(정답 수, 전체 문항 수) 반환."""
    correct = sum(1 for a in answers if a.is_correct)
    return correct, len(answers)
