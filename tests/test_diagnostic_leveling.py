"""레벨 판정 순수 로직 단위 테스트 (DB 불필요).

판정 규칙은 잠정 — 이 테스트는 *의도된 잠정 규칙*을 고정한다 (확정 시 갱신).
"""

from src.domains.quiz.util import GradedAnswer
from src.domains.quiz.util import (
    diagnose_level,
    level_accuracies,
)


def _answers(spec: list[tuple[str, bool]]) -> list[GradedAnswer]:
    out: list[GradedAnswer] = []
    for i, (level, correct) in enumerate(spec):
        out.append(
            GradedAnswer(
                question_key=f"q_{level}_{i}",
                grammar_point_id=f"grammar_{level}_{i:03d}",
                level=level,
                selected_choice="A",
                correct_choice="A" if correct else "B",
                is_correct=correct,
            )
        )
    return out


def test_level_accuracies() -> None:
    acc = level_accuracies(_answers([("N5", True), ("N5", False), ("N4", True)]))
    assert acc["N5"] == 0.5
    assert acc["N4"] == 1.0


def test_diagnose_picks_hardest_passed_level() -> None:
    # N5 100%, N4 100%, N3 0% → N4 (통과한 가장 어려운 레벨)
    answers = _answers(
        [("N5", True), ("N5", True), ("N4", True), ("N4", True), ("N3", False)]
    )
    assert diagnose_level(answers) == "N4"


def test_diagnose_all_correct_returns_hardest() -> None:
    answers = _answers([("N5", True), ("N4", True), ("N3", True)])
    assert diagnose_level(answers) == "N3"


def test_diagnose_none_passes_returns_none() -> None:
    answers = _answers([("N5", False), ("N5", False), ("N4", False)])
    assert diagnose_level(answers) is None


def test_diagnose_empty_returns_none() -> None:
    assert diagnose_level([]) is None


def test_diagnose_threshold_boundary() -> None:
    # N5 정답률 정확히 0.6 (3/5) → 기본 threshold 0.6 이상이라 통과.
    answers = _answers(
        [("N5", True), ("N5", True), ("N5", True), ("N5", False), ("N5", False)]
    )
    assert diagnose_level(answers) == "N5"
    # threshold 0.7 이면 미통과 → None.
    assert diagnose_level(answers, threshold=0.7) is None
