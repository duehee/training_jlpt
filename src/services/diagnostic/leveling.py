"""레벨 판정 — 순수 로직 (DB/LLM 무관).

⚠️ 판정 규칙은 **잠정(provisional)**이다. 정빈님과 확정 전 합리적 기본값:
  레벨별 정답률 >= PASS_THRESHOLD 이면 그 레벨 '통과' →
  통과한 레벨 중 가장 어려운(높은) 레벨을 diagnosed_level 로 본다.
  아무 레벨도 통과 못하면 None (가장 쉬운 레벨 미만).

Phase 1 범위는 N5~N3 (CLAUDE.md §프로젝트 개요). 난이도 순서는 N5(쉬움) < N3(어려움).
규칙을 교체하기 쉽도록 threshold를 인자로 노출한다.
"""

from __future__ import annotations

from src.services.diagnostic.scoring import GradedAnswer

# 통과 기준 정답률 (잠정).
PASS_THRESHOLD = 0.6

# 레벨 난이도 순위 (클수록 어려움). JLPT는 N5가 가장 쉽다.
_LEVEL_ORDER: dict[str, int] = {"N5": 1, "N4": 2, "N3": 3, "N2": 4, "N1": 5}


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
