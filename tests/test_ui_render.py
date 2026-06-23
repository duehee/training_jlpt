"""UI 순수 헬퍼 + API 에러 매핑 단위 테스트 (DB/네트워크/Streamlit 비의존).

view 위젯 자체는 비대상 — 변환·판정 로직만 검증한다 (페르소나 §4 "얇은 프론트").
"""

from __future__ import annotations

from src.ui.api_client import ApiError, parse_error_payload
from src.ui.render import (
    cached_badge,
    choice_label,
    default_selected_point,
    friendly_error,
    level_label,
    partition_weak_points,
    split_example,
    stem_display,
)


# ── render: level_label (잠정 톤 + null) ──
def test_level_label_none_is_unjudged() -> None:
    assert "미판정" in level_label(None)
    assert "미판정" in level_label("")


def test_level_label_marks_provisional() -> None:
    # 잠정 규칙이라 '확정'으로 단정하지 않는다 (base 01 §2-2).
    assert level_label("N4") == "N4 (잠정)"


# ── render: stem_display (furigana null-safe) ──
def test_stem_display_prefers_furigana() -> None:
    q = {"prompt": "食べる", "prompt_furigana": "<ruby>食<rt>た</rt></ruby>べる"}
    assert stem_display(q) == "<ruby>食<rt>た</rt></ruby>べる"


def test_stem_display_falls_back_to_prompt_when_null() -> None:
    # 수진 v2 데이터 적재 전: furigana null → 일본어 prompt 폴백 (안 깨짐).
    assert stem_display({"prompt": "私は学生です。", "prompt_furigana": None}) == "私は学生です。"
    assert stem_display({"prompt": "雨が降る"}) == "雨が降る"


# ── render: choice_label (한국어 병기 null-safe) ──
def test_choice_label_with_ko() -> None:
    assert choice_label({"key": "A", "text": "は", "text_ko": "는"}) == "A. は (는)"


def test_choice_label_without_ko() -> None:
    # text_ko 키 생략 시 일본어만.
    assert choice_label({"key": "B", "text": "が"}) == "B. が"


# ── render: cached_badge ──
def test_cached_badge() -> None:
    assert "적중" in cached_badge(True)
    assert "신규" in cached_badge(False)


# ── render: split_example ("jp — ko") ──
def test_split_example_with_separator() -> None:
    jp, ko = split_example("彼が学生です。 — 그가 학생입니다.")
    assert jp == "彼が学生です。"
    assert ko == "그가 학생입니다."


def test_split_example_without_separator() -> None:
    jp, ko = split_example("彼が学生です。")
    assert jp == "彼が学生です。"
    assert ko == ""


# ── render: 약점 분리 (N5 설명가능 / N4 보류) ──
def _weak(gid: str, level: str) -> dict[str, object]:
    return {"grammar_point_id": gid, "level": level, "error_count": 1}


def test_partition_weak_points_splits_by_level() -> None:
    weak = [_weak("grammar_n5_011", "N5"), _weak("grammar_n4_023", "N4")]
    explainable, deferred = partition_weak_points(weak)
    assert [w["grammar_point_id"] for w in explainable] == ["grammar_n5_011"]
    assert [w["grammar_point_id"] for w in deferred] == ["grammar_n4_023"]


def test_default_selected_point_prefers_explainable() -> None:
    weak = [_weak("grammar_n4_023", "N4"), _weak("grammar_n5_011", "N5")]
    # N4가 앞에 있어도 설명 가능한 N5를 기본 선택해 happy path 유지.
    assert default_selected_point(weak) == "grammar_n5_011"


def test_default_selected_point_none_when_no_explainable() -> None:
    assert default_selected_point([_weak("grammar_n4_023", "N4")]) is None
    assert default_selected_point([]) is None


# ── render: friendly_error 매핑 ──
def test_friendly_error_known_codes() -> None:
    assert "만료" in friendly_error(401)
    assert "연결" in friendly_error(0)
    assert "준비" in friendly_error(404)


def test_friendly_error_unknown_code_has_fallback() -> None:
    assert friendly_error(418) != ""


# ── api_client: 에러 페이로드 파싱 ──
def test_parse_error_contract_format() -> None:
    raw = '{"error": {"code": "DIAGNOSTIC_SESSION_NOT_FOUND", "message": "진단 세션 없음"}}'
    err = parse_error_payload(404, raw)
    assert isinstance(err, ApiError)
    assert err.status_code == 404
    assert err.code == "DIAGNOSTIC_SESSION_NOT_FOUND"
    assert err.message == "진단 세션 없음"


def test_parse_error_fastapi_detail_format() -> None:
    err = parse_error_payload(409, '{"detail": "이미 완료됨"}')
    assert err.message == "이미 완료됨"


def test_parse_error_non_json_body() -> None:
    err = parse_error_payload(500, "Internal Server Error")
    assert err.status_code == 500
    assert err.message == "Internal Server Error"
