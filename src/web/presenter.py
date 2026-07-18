"""순수 shaping 헬퍼 — 실 진단 데이터 → design_backend 시안 컨텍스트 형상.

DB/IO 무관 순수 함수 (domains/quiz 의 순수/DB 분리 패턴 계승).
시안 `design_backend/main.py` 의 컨텍스트 생성 로직을 1:1로 옮긴다.
"""

from __future__ import annotations

from typing import Any

from src.domains.quiz.dto.response import ClientQuestion, WeakGrammarPoint

# 레벨 색 토큰 (시안 data.py `lv()` 1:1: N5/N4/N3). 그 외 레벨은 N5로 폴백.
_LEVEL_TOKENS: dict[str, tuple[str, str]] = {
    "N5": ("#2f55d4", "#eaeefb"),
    "N4": ("#0f9d6b", "#e7f6ef"),
    "N3": ("#d98324", "#fbf0df"),
}
_DEFAULT_LEVEL = "N5"

_CHOICE_LABELS: tuple[str, ...] = ("A", "B", "C", "D", "E", "F")


def level_color(level: str | None) -> tuple[str, str]:
    """레벨 → (글자색, 배경색). 미지정/미지원 레벨은 N5 토큰으로 폴백."""
    return _LEVEL_TOKENS.get(level or _DEFAULT_LEVEL, _LEVEL_TOKENS[_DEFAULT_LEVEL])


def progress_pct(index: int, total: int) -> str:
    """1-based 진행률 문자열 `"NN%"` (시안 main.py:156)."""
    if total <= 0:
        return "0%"
    return f"{round((index + 1) / total * 100)}%"


def shape_choices(
    choices: list[dict[str, Any]], selected_idx: int
) -> list[dict[str, Any]]:
    """실 API `[{key,text,text_ko?}]` → 시안 choice 형상(선택 하이라이트 포함).

    선택 색 계산은 여기(라우터 측)에서 수행 → 템플릿은 받은 토큰만 사용(얇은 프론트).
    색값은 시안 main.py:140-149 1:1. `text_ko` 없으면 `ko`=None → 템플릿이 숨김.
    """
    shaped: list[dict[str, Any]] = []
    for k, choice in enumerate(choices):
        on = k == selected_idx
        shaped.append(
            {
                "label": _CHOICE_LABELS[k] if k < len(_CHOICE_LABELS) else str(k + 1),
                "jp": choice.get("text", ""),
                "ko": choice.get("text_ko"),
                "k": k,
                "bg": "#eef2fd" if on else "#fff",
                "border": "#2f55d4" if on else "#e2e5ea",
                "dotBorder": "#2f55d4" if on else "#cfd4dc",
                "dotBg": "#2f55d4" if on else "#fff",
                "labelColor": "#fff" if on else "#9298a2",
            }
        )
    return shaped


def selected_choice_key(question: ClientQuestion, selected_idx: int) -> str | None:
    """선택 인덱스 → 선택지 key. 범위 밖이면 None."""
    if 0 <= selected_idx < len(question.choices):
        key = question.choices[selected_idx].get("key")
        return str(key) if key is not None else None
    return None


def quiz_context(
    question: ClientQuestion,
    *,
    index: int,
    total: int,
    selected_idx: int,
) -> dict[str, Any]:
    """quiz.html 컨텍스트 (user 제외 — 라우터가 base 컨텍스트로 병합)."""
    color, bg = level_color(question.level)
    can_next = selected_idx >= 0
    is_last = index == total - 1
    return {
        "i": index,
        "sel": selected_idx,
        "q_num": index + 1,
        "q_total": total,
        "q_level": question.level,
        "q_level_color": color,
        "q_level_bg": bg,
        "progress_pct": progress_pct(index, total),
        "prompt_furigana": question.prompt_furigana,
        "prompt": question.prompt,
        "ko": question.prompt_ko,
        "choices": shape_choices(question.choices, selected_idx),
        "can_next": can_next,
        "next_label": "채점하기" if is_last else "다음 문항",
        "next_bg": "#2f55d4" if can_next else "#e2e5ea",
        "next_color": "#fff" if can_next else "#aab0bb",
    }


def auth_context(mode: str) -> dict[str, Any]:
    """login.html 화면 컨텍스트 (mode=login|signup). 순수 카피/분기값만.

    슬롯(error/notice/form_* 등)은 라우터가 상황별로 채운다 — 여기선 mode 고정 텍스트만.
    """
    if mode == "signup":
        return {
            "signup": True,
            "auth_title": "회원가입",
            "auth_sub": "이메일로 가입하고 진단 기록을 저장하세요.",
            "auth_cta": "회원가입",
            "auth_switch_text": "이미 계정이 있으신가요?",
            "auth_switch_mode": "login",
            "auth_switch_cta": "로그인",
        }
    return {
        "signup": False,
        "auth_title": "로그인",
        "auth_sub": "다시 오신 걸 환영해요. 이메일로 로그인하세요.",
        "auth_cta": "로그인",
        "auth_switch_text": "아직 계정이 없으신가요?",
        "auth_switch_mode": "signup",
        "auth_switch_cta": "회원가입",
    }


def verify_context(status: str) -> dict[str, Any]:
    """verify.html 화면 컨텍스트 (status=success|expired|invalid). 순수 카피/분기.

    엣지(만료/무효)에서 사용자가 막히지 않게 재발송/로그인 동선 플래그를 함께 준다
    (정빈님 UX 지시). email 슬롯은 라우터가 채운다(성공 시 확인된 이메일).
    """
    if status == "success":
        return {
            "status": "success",
            "verify_title": "이메일 확인 완료",
            "verify_body": "이제 로그인하고 진단 기록을 이어갈 수 있어요.",
            "show_login": True,
            "show_resend": False,
        }
    if status == "expired":
        return {
            "status": "expired",
            "verify_title": "링크가 만료됐어요",
            "verify_body": "확인 링크는 24시간 동안만 유효해요. 이메일을 입력하면 새 링크를 보내드릴게요.",
            "show_login": False,
            "show_resend": True,
        }
    return {
        "status": "invalid",
        "verify_title": "유효하지 않은 링크예요",
        "verify_body": "이미 사용됐거나 잘못된 링크예요. 이미 확인했다면 로그인하고, 아니면 새 링크를 받아보세요.",
        "show_login": True,
        "show_resend": True,
    }


def shape_weak_list(
    weak_points: list[WeakGrammarPoint], enrich: dict[str, dict[str, str | None]]
) -> list[dict[str, Any]]:
    """약점 포인트 → 시안 weak_list 형상. enrich(gp_id→{jp,sub})는 라우터가 DB 조회.

    enrich 미존재(N4 등 chunk 미적재) → jp/sub None → 하린 §5 폴백이 카드 유지.
    explain 미이식이라 cta는 전부 '곧 추가' 톤.
    """
    shaped: list[dict[str, Any]] = []
    for point in weak_points:
        color, bg = level_color(point.level)
        meta = enrich.get(point.grammar_point_id, {})
        shaped.append(
            {
                "id": point.grammar_point_id,
                "jp": meta.get("jp"),
                "sub": meta.get("sub"),
                "level": point.level,
                "levelColor": color,
                "levelBg": bg,
                "cta": "곧 추가",
                "ctaColor": "#b6bcc6",
            }
        )
    return shaped


def result_copy(perfect: bool, diagnosed_level: str | None) -> str:
    """진단 결과 카피 (시안 main.py:196-202 1:1)."""
    if perfect:
        return "모든 문항을 정확히 맞혔어요. 한 단계 위 레벨에 도전해 보세요."
    if diagnosed_level:
        return (
            "정답률 60% 이상 통과 중 가장 높은 레벨 기준으로 잠정 산정했어요. "
            "아래 약점 문법을 보완하면 다음 레벨로 올라갈 수 있어요."
        )
    return "이번 진단으로는 레벨이 확정되지 않았어요. 기초 문법부터 차근차근 추천드릴게요."


def recommendation(
    perfect: bool,
    recommended_start_point: str | None,
    enrich: dict[str, dict[str, str | None]],
) -> tuple[str, str]:
    """추천 학습 시작점 (제목, 본문). 시안 main.py:217-220 패턴 + 실 추천 포인트 반영."""
    if perfect:
        return (
            "N4 문법 입문",
            "진단을 통과했어요. N4 핵심 문법 50선으로 넘어가 보세요.",
        )
    if recommended_start_point:
        sub = enrich.get(recommended_start_point, {}).get("sub")
        title = f"{sub} 집중 학습" if sub else "약점 문법 집중 학습"
        return (
            title,
            "약점으로 나온 문법부터 복습하면 점수가 가장 빠르게 오릅니다.",
        )
    return (
        "기초 문법부터 복습",
        "기초 문법부터 차근차근 복습하면 다음 진단에서 레벨이 잡힙니다.",
    )
