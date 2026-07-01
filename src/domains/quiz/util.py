"""진단(quiz) 순수 계산 — DB/LLM 무관 (단위 테스트 대상).

채점(scoring) + 레벨 판정(leveling) + 약점 도출을 한곳에 모은다.
DB 접근·흐름 오케스트레이션은 service.py 참조.

⚠️ 레벨 판정 규칙은 **잠정(provisional)** — 정빈님과 확정 전 합리적 기본값
  (레벨별 정답률 >= PASS_THRESHOLD 통과 → 통과 레벨 중 최상위를 diagnosed_level).
"""

from __future__ import annotations

from pydantic import BaseModel

# 본 사이클 진단 출제 레벨 (N5 적재 + N4 진단 문항). 셔플 없음(결정적, 정빈님 D-셔플).
DIAGNOSTIC_LEVELS: tuple[str, ...] = ("N5", "N4")

# 통과 기준 정답률 (잠정).
PASS_THRESHOLD = 0.6

# 레벨 난이도 순위 (클수록 어려움). JLPT는 N5가 가장 쉽다.
_LEVEL_ORDER: dict[str, int] = {"N5": 1, "N4": 2, "N3": 3, "N2": 4, "N1": 5}


# ── 채점 (scoring) ──
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


# ── 레벨 판정 (leveling) ──
def level_accuracies(answers: list[GradedAnswer]) -> dict[str, float]:
    """레벨별 정답률. 해당 레벨 문항이 없으면 키 자체가 없다."""
    totals: dict[str, int] = {}
    corrects: dict[str, int] = {}
    for a in answers:
        totals[a.level] = totals.get(a.level, 0) + 1
        if a.is_correct:
            corrects[a.level] = corrects.get(a.level, 0) + 1
    return {lvl: corrects.get(lvl, 0) / n for lvl, n in totals.items()}


def diagnose_level(
    answers: list[GradedAnswer], *, threshold: float = PASS_THRESHOLD
) -> str | None:
    """채점 결과 → diagnosed_level (잠정 규칙). 통과 레벨 없으면 None."""
    if not answers:
        return None
    accuracies = level_accuracies(answers)
    passed = [lvl for lvl, acc in accuracies.items() if acc >= threshold]
    if not passed:
        return None
    # 통과한 레벨 중 가장 어려운 레벨.
    return max(passed, key=lambda lvl: _LEVEL_ORDER.get(lvl, 0))


# ── 약점 도출 ──
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
