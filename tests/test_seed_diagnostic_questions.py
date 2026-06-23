"""진단 문항 seed 로드·검증 단위 테스트 (DB 불필요).

적재 전 순수 검증(정답 무결성·분포·레벨)을 고정한다. 실 DB UPSERT는 별도(통합).
"""

from collections import Counter

import pytest
from pydantic import ValidationError

from scripts.seed_diagnostic_questions import (
    DEFAULT_SEED,
    QuestionSeed,
    load_seed,
)

# 학습 루프 보안 불변식 회귀: 진단 출제 직렬화에 정답이 새지 않아야 한다.
from src.services.diagnostic.flow import to_client_question
from src.db.models import DiagnosticQuestion


def test_default_seed_loads_ten() -> None:
    questions = load_seed(DEFAULT_SEED)
    assert len(questions) == 10


def test_answer_distribution_a2_b2_c3_d3() -> None:
    """v1.5 정답 분포 고정 (사사키 row 정합 PASS 기준)."""
    questions = load_seed(DEFAULT_SEED)
    dist = Counter(q.correct_choice for q in questions)
    assert dist == {"A": 2, "B": 2, "C": 3, "D": 3}


def test_level_split_n5_5_n4_5() -> None:
    questions = load_seed(DEFAULT_SEED)
    dist = Counter(q.level for q in questions)
    assert dist == {"N5": 5, "N4": 5}


def test_every_correct_choice_in_choice_keys() -> None:
    """정답 무결성 — correct_choice는 반드시 choices 키 집합에 존재."""
    for q in load_seed(DEFAULT_SEED):
        keys = {c.key for c in q.choices}
        assert q.correct_choice in keys


def test_question_keys_unique_and_formatted() -> None:
    questions = load_seed(DEFAULT_SEED)
    keys = [q.question_key for q in questions]
    assert len(set(keys)) == len(keys)
    for k in keys:
        assert k.startswith("q_n")


def test_reject_correct_choice_not_in_choices() -> None:
    """정답이 선택지에 없으면 검증 단계에서 차단."""
    bad = {
        "question_key": "q_n5_999",
        "level": "N5",
        "grammar_point_id": "grammar_n5_001",
        "stem": "___",
        "choices": [
            {"key": "A", "text": "は"},
            {"key": "B", "text": "が"},
            {"key": "C", "text": "を"},
            {"key": "D", "text": "に"},
        ],
        "correct_choice": "Z",
    }
    with pytest.raises(ValidationError):
        QuestionSeed.model_validate(bad)


def test_reject_non_four_choices() -> None:
    bad = {
        "question_key": "q_n5_998",
        "level": "N5",
        "grammar_point_id": "grammar_n5_001",
        "stem": "___",
        "choices": [{"key": "A", "text": "は"}, {"key": "B", "text": "が"}],
        "correct_choice": "A",
    }
    with pytest.raises(ValidationError):
        QuestionSeed.model_validate(bad)


def test_reject_bad_level() -> None:
    bad = {
        "question_key": "q_x_001",
        "level": "N9",
        "grammar_point_id": "grammar_x_001",
        "stem": "___",
        "choices": [
            {"key": "A", "text": "1"},
            {"key": "B", "text": "2"},
            {"key": "C", "text": "3"},
            {"key": "D", "text": "4"},
        ],
        "correct_choice": "A",
    }
    with pytest.raises(ValidationError):
        QuestionSeed.model_validate(bad)


def test_seed_to_client_question_excludes_answer() -> None:
    """seed → ORM → 클라 직렬화에 정답이 노출되지 않아야 한다 (flow 불변식 회귀)."""
    q = load_seed(DEFAULT_SEED)[0]
    row = q.to_row()
    orm = DiagnosticQuestion(
        question_key=row["question_key"],
        level=row["level"],
        grammar_point_id=row["grammar_point_id"],
        stem=row["stem"],
        choices=row["choices"],
        correct_choice=row["correct_choice"],
    )
    dumped = to_client_question(orm).model_dump_json()
    # 정답 '필드'가 직렬화에 없어야 한다. (correct_choice 값 A/B/C/D는 choices 키로
    # 정상 노출되며, 어느 키가 정답인지는 드러나지 않으므로 누출이 아니다 — 정빈님 불변식과 동일.)
    assert "correct_choice" not in dumped
    assert "correct" not in dumped
