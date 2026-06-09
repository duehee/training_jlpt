"""진단 채점 순수 로직 단위 테스트 (DB 불필요)."""

from src.services.diagnostic.scoring import (
    GradedAnswer,
    aggregate_score,
    grade_answer,
)


def _ans(level: str, correct: bool) -> GradedAnswer:
    return GradedAnswer(
        question_key=f"q_{level}",
        grammar_point_id=f"grammar_{level}_001",
        level=level,
        selected_choice="A",
        correct_choice="A" if correct else "B",
        is_correct=correct,
    )


def test_grade_answer_correct() -> None:
    g = grade_answer(
        question_key="q_n5_001",
        grammar_point_id="grammar_n5_001",
        level="N5",
        selected_choice="A",
        correct_choice="A",
    )
    assert g.is_correct is True


def test_grade_answer_incorrect() -> None:
    g = grade_answer(
        question_key="q_n5_001",
        grammar_point_id="grammar_n5_001",
        level="N5",
        selected_choice="C",
        correct_choice="A",
    )
    assert g.is_correct is False


def test_aggregate_score() -> None:
    answers = [_ans("N5", True), _ans("N5", False), _ans("N4", True)]
    assert aggregate_score(answers) == (2, 3)


def test_aggregate_score_empty() -> None:
    assert aggregate_score([]) == (0, 0)
