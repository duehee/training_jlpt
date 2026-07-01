"""진단 흐름 순수 로직 단위 테스트 (DB 불필요).

보안 핵심: 클라 직렬화에 정답(correct_choice)이 새지 않아야 한다.
"""

from src.db.models import DiagnosticQuestion
from src.domains.quiz.service import to_client_question
from src.domains.quiz.util import GradedAnswer, derive_weak_point_ids


def _question() -> DiagnosticQuestion:
    return DiagnosticQuestion(
        question_key="q_n5_001",
        level="N5",
        grammar_point_id="grammar_n5_001",
        stem="私___学生です。",
        choices=[
            {"key": "A", "text": "は"},
            {"key": "B", "text": "が"},
            {"key": "C", "text": "を"},
            {"key": "D", "text": "に"},
        ],
        correct_choice="A",
    )


def test_to_client_question_excludes_answer() -> None:
    cq = to_client_question(_question())
    assert cq.question_id == "q_n5_001"
    assert cq.grammar_point_id == "grammar_n5_001"
    assert cq.level == "N5"
    assert len(cq.choices) == 4
    # 정답이 직렬화 결과 어디에도 노출되지 않아야 한다.
    dumped = cq.model_dump_json()
    assert "correct_choice" not in dumped
    assert "correct" not in dumped


def _ga(gp: str, correct: bool) -> GradedAnswer:
    return GradedAnswer(
        question_key=f"q_{gp}",
        grammar_point_id=gp,
        level="N5",
        selected_choice="A",
        correct_choice="A" if correct else "B",
        is_correct=correct,
    )


def test_derive_weak_points_only_incorrect_unique_ordered() -> None:
    answers = [
        _ga("grammar_n5_001", False),
        _ga("grammar_n5_002", True),
        _ga("grammar_n5_003", False),
        _ga("grammar_n5_001", False),  # 중복 → 한 번만
    ]
    assert derive_weak_point_ids(answers) == [
        "grammar_n5_001",
        "grammar_n5_003",
    ]


def test_derive_weak_points_all_correct_empty() -> None:
    answers = [_ga("grammar_n5_001", True), _ga("grammar_n5_002", True)]
    assert derive_weak_point_ids(answers) == []
