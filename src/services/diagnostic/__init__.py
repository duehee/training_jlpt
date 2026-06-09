"""진단(레벨 판정) 도메인 서비스.

학습 루프의 입력(약점)을 만드는 선행 단계. 4지선다 규칙 채점 → 레벨 판정 →
약점 도출. LLM 미사용. 정식 진단 문항(diagnostic_questions) 도착 시 완전 동작하는
뼈대 (현재 문항 0건).

- `scoring`  : 채점 순수 로직
- `leveling` : 레벨 판정 순수 로직 (규칙 잠정)
- `flow`     : 출제 직렬화(정답 제외) + DB 래퍼 + 약점 도출
"""

from __future__ import annotations

from src.services.diagnostic.flow import (
    ClientQuestion,
    derive_weak_point_ids,
    fetch_questions,
    record_answer,
    to_client_question,
)
from src.services.diagnostic.leveling import (
    PASS_THRESHOLD,
    diagnose_level,
    level_accuracies,
)
from src.services.diagnostic.scoring import (
    GradedAnswer,
    aggregate_score,
    grade_answer,
)

__all__ = [
    "GradedAnswer",
    "grade_answer",
    "aggregate_score",
    "diagnose_level",
    "level_accuracies",
    "PASS_THRESHOLD",
    "ClientQuestion",
    "to_client_question",
    "derive_weak_point_ids",
    "fetch_questions",
    "record_answer",
]
