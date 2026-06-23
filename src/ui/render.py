"""순수 렌더 헬퍼 (view 로직, Streamlit 비의존 — 단위 테스트 대상).

화면 표시에 필요한 변환/판정만 담는다. 실제 위젯 렌더는 `app.py`.
모든 함수는 부수효과 없는 순수 함수다.
"""

from __future__ import annotations

from typing import Any

# 현재 적재 레벨 (본 세션 = N5만). 이 레벨의 약점만 explanation chunk가 있다.
EXPLAINABLE_LEVELS: frozenset[str] = frozenset({"N5"})

# 에러 status_code → 사용자용 한국어 메시지. 각 메시지는 "다음 행동" 1개를 함의한다.
_ERROR_MESSAGES: dict[int, str] = {
    0: "API 서버에 연결할 수 없습니다. 서버 실행 여부를 확인하고 다시 시도해 주세요.",
    400: "요청에 문제가 있습니다. 진단을 다시 시도해 주세요.",
    401: "세션이 만료됐어요. 진단을 처음부터 다시 시작합니다.",
    404: "이 항목의 데이터가 아직 준비되지 않았습니다.",
    409: "이미 처리된 요청입니다. 화면을 새로고침해 주세요.",
    500: "일시적인 서버 오류입니다. 잠시 후 다시 시도해 주세요.",
    503: "진단 문항이 아직 준비 중입니다. 데이터 적재 후 이용할 수 있습니다.",
}


def friendly_error(status_code: int) -> str:
    """API status_code를 사용자가 읽을 한국어 메시지로 매핑."""
    return _ERROR_MESSAGES.get(status_code, "알 수 없는 오류가 발생했습니다. 다시 시도해 주세요.")


def stem_display(question: dict[str, Any]) -> str:
    """문항 stem 표시 HTML — furigana(ruby) 있으면 우선, 없으면 plain prompt.

    null-safe: `prompt_furigana`가 없거나 비면 일본어 `prompt`로 자연 폴백
    (수진 v2 데이터 적재 전에도 안 깨짐, 재현 schema close 권장).
    """
    furigana = question.get("prompt_furigana")
    if furigana:
        return str(furigana)
    return str(question.get("prompt", ""))


def choice_label(choice: dict[str, Any]) -> str:
    """라디오 옵션 라벨 — 'A. は' + 한국어 병기(text_ko 있으면 'A. は (는)').

    `text_ko`가 없으면(키 생략) 일본어만 표시 (null-safe).
    """
    base = f"{choice['key']}. {choice['text']}"
    text_ko = choice.get("text_ko")
    if text_ko:
        return f"{base} ({text_ko})"
    return base


def level_label(diagnosed_level: str | None) -> str:
    """진단 레벨 표시 문구. 잠정 규칙이라 '확정'으로 단정하지 않는다 (base 01 §2-2)."""
    if not diagnosed_level:
        return "레벨 미판정 (기초부터 추천)"
    return f"{diagnosed_level} (잠정)"


def cached_badge(cached: bool) -> str:
    """캐시 적중 여부 배지 — 캐시 레이어 동작 가시화."""
    return "캐시 적중 ✅" if cached else "신규 생성 ⚡"


def split_example(example: str) -> tuple[str, str]:
    """LLM 예문 문자열 'jp — ko'를 (일본어, 한국어)로 분리.

    구분자 '—'(em dash)가 없으면 (원문, "")을 반환한다.
    """
    if "—" in example:
        jp, _, ko = example.partition("—")
        return jp.strip(), ko.strip()
    return example.strip(), ""


def partition_weak_points(
    weak_points: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """약점 포인트를 (설명 가능, 설명 보류)로 분리.

    설명 가능 = EXPLAINABLE_LEVELS(현재 N5). 그 외(N4 등)는 chunk 미적재 → 404 빈 상태.
    happy path가 N5 약점으로 흐르도록 결과 화면이 설명 가능 약점을 기본 선택한다.
    """
    explainable = [w for w in weak_points if w.get("level") in EXPLAINABLE_LEVELS]
    deferred = [w for w in weak_points if w.get("level") not in EXPLAINABLE_LEVELS]
    return explainable, deferred


def default_selected_point(weak_points: list[dict[str, Any]]) -> str | None:
    """결과 화면 기본 선택 약점 — 설명 가능(N5) 우선, 없으면 None."""
    explainable, _ = partition_weak_points(weak_points)
    if explainable:
        return str(explainable[0]["grammar_point_id"])
    return None
