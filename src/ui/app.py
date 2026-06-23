"""JLPT 진단 데모 — Streamlit 1 화면 (트랙 X3).

실행: poetry run streamlit run src/ui/app.py  (API 서버가 먼저 떠 있어야 함)

설계 (docs/planning/session_6/fe_harin/01_screen_flow_sketch.md v3):
- 게스트 우선: 로그인 없이 진단 → 결과 → RAG 설명까지 한 사이클.
- 동작 가시화 1순위: retrieved(DB 원본·사실) vs generated_explanation/examples(LLM 가공) 시각 분리 + cached 배지.
- 상태 강제: 로딩 / 에러(401·400·404·409·5xx) / 빈 결과(레벨 null·약점 0·N4 404) 모두 처리.
얇은 프론트 — 모든 로직은 API 뒤. 이 파일은 view + 단계 전환만.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.ui.api_client import ApiClient, ApiError
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

# ── 단계 상수 ──
STAGE_INTRO = "intro"
STAGE_QUIZ = "quiz"
STAGE_RESULT = "result"

_JP_STYLE = """
<style>
.jp-text { font-size: 1.15rem; line-height: 1.9; }
.jp-sub { color: #6b7280; font-size: 0.85rem; }
</style>
"""


def _init_state() -> None:
    ss = st.session_state
    ss.setdefault("stage", STAGE_INTRO)
    ss.setdefault("client", ApiClient())
    ss.setdefault("diag_id", None)
    ss.setdefault("questions", [])
    ss.setdefault("q_index", 0)
    ss.setdefault("result", None)
    ss.setdefault("selected_gid", None)
    ss.setdefault("explanation", None)


def _reset_to_intro() -> None:
    """세션 만료 등으로 처음부터 다시 시작."""
    for key in ("diag_id", "questions", "result", "selected_gid", "explanation"):
        st.session_state[key] = [] if key == "questions" else None
    st.session_state["q_index"] = 0
    st.session_state["client"] = ApiClient()
    st.session_state["stage"] = STAGE_INTRO


def _handle_api_error(exc: ApiError) -> None:
    """에러를 사용자 메시지로 표시. 401은 처음부터 재시작 유도."""
    st.error(f"⚠️ {friendly_error(exc.status_code)}")
    if exc.status_code == 401:
        if st.button("진단 다시 시작"):
            _reset_to_intro()
            st.rerun()


# ── intro ──
def _render_intro() -> None:
    st.subheader("일본어 문법 약점, AI가 진단해 드려요")
    st.write(
        "로그인 없이 바로 체험할 수 있습니다. 10문항을 풀면 약점 문법을 찾아 "
        "**검색된 근거(chunk)** 위에서 AI가 설명합니다."
    )
    if st.button("진단 시작", type="primary"):
        client: ApiClient = st.session_state["client"]
        try:
            with st.spinner("진단을 준비하고 있어요…"):
                client.create_anonymous_session()
                diag = client.start_diagnosis()
                questions = client.get_questions(diag["diagnostic_session_id"])
            st.session_state["diag_id"] = diag["diagnostic_session_id"]
            st.session_state["questions"] = questions.get("questions", [])
            st.session_state["q_index"] = 0
            st.session_state["stage"] = STAGE_QUIZ
            st.rerun()
        except ApiError as exc:
            _handle_api_error(exc)


# ── quiz ──
def _render_quiz() -> None:
    questions: list[dict[str, Any]] = st.session_state["questions"]
    total = len(questions)
    if total == 0:  # 빈 결과: 출제 문항 0건 (미적재)
        st.info("진단 문항이 아직 준비 중입니다. 데이터 적재 후 다시 이용해 주세요.")
        if st.button("처음으로"):
            _reset_to_intro()
            st.rerun()
        return

    idx = st.session_state["q_index"]
    q = questions[idx]
    st.progress((idx) / total, text=f"{idx + 1} / {total} 문항")
    st.caption(f"{q['level']} · {q['grammar_point_id']}")
    st.markdown(f"<div class='jp-text'>{stem_display(q)}</div>", unsafe_allow_html=True)
    if q.get("prompt_ko"):  # 한국어 번역 보조 (학습자 가독성, 절제된 보조 표시)
        st.markdown(f"<div class='jp-sub'>{q['prompt_ko']}</div>", unsafe_allow_html=True)

    choices = q["choices"]
    labels = [choice_label(c) for c in choices]
    picked = st.radio("알맞은 것을 고르세요", labels, key=f"q_{q['question_id']}", index=None)

    is_last = idx == total - 1
    btn_label = "제출하고 결과 보기" if is_last else "다음 문항"
    if st.button(btn_label, type="primary", disabled=picked is None) and picked is not None:
        selected_key = picked.split(".")[0]
        client: ApiClient = st.session_state["client"]
        diag_id = st.session_state["diag_id"]
        try:
            with st.spinner("채점 중…"):
                try:
                    client.submit_answer(diag_id, q["question_id"], selected_key)
                except ApiError as exc:
                    if exc.status_code != 409:  # 409=이미 제출 → 멱등 진행
                        raise
                if is_last:
                    st.session_state["result"] = client.complete(diag_id)
                    st.session_state["selected_gid"] = default_selected_point(
                        st.session_state["result"].get("weak_grammar_points", [])
                    )
                    st.session_state["stage"] = STAGE_RESULT
                else:
                    st.session_state["q_index"] = idx + 1
            st.rerun()
        except ApiError as exc:
            _handle_api_error(exc)


# ── result + explanation ──
def _render_result() -> None:
    result: dict[str, Any] = st.session_state["result"]
    st.subheader("진단 결과")
    col1, col2 = st.columns(2)
    col1.metric("진단 레벨", level_label(result.get("diagnosed_level")))
    col2.metric("점수", f"{result.get('score', 0)} / {result.get('max_score', 0)}")

    weak = result.get("weak_grammar_points", [])
    if not weak:  # 빈 결과: 만점
        st.success("약점이 발견되지 않았습니다 🎉 아주 잘하고 계세요!")
        _restart_button()
        return

    explainable, deferred = partition_weak_points(weak)
    st.markdown("#### 약점 문법 — 클릭하면 설명을 봅니다")
    for w in explainable:
        gid = w["grammar_point_id"]
        if st.button(f"📌 {gid} ({w['level']}) · 오답 {w['error_count']}회", key=f"w_{gid}"):
            _load_explanation(gid)

    for w in deferred:  # N4 등: chunk 미적재 → 설명 보류
        st.button(
            f"🔒 {w['grammar_point_id']} ({w['level']}) · 설명 곧 추가",
            key=f"d_{w['grammar_point_id']}",
            disabled=True,
        )
        st.caption("이 레벨의 설명 데이터는 이후 적재 예정입니다.")

    if st.session_state.get("selected_gid"):
        st.divider()
        _render_explanation()

    _restart_button()


def _load_explanation(gid: str) -> None:
    client: ApiClient = st.session_state["client"]
    diag_id = st.session_state["diag_id"]
    st.session_state["selected_gid"] = gid
    try:
        with st.spinner("AI가 검색된 근거로 문법 설명을 생성 중…"):
            st.session_state["explanation"] = client.get_explanation(diag_id, gid)
    except ApiError as exc:
        st.session_state["explanation"] = None
        if exc.status_code == 404:  # 빈 결과: chunk 미적재
            st.session_state["explanation"] = {"_empty": True}
        else:
            _handle_api_error(exc)
    st.rerun()


def _render_explanation() -> None:
    exp = st.session_state.get("explanation")
    if not exp:
        return
    if exp.get("_empty"):
        st.info("이 문법 포인트의 설명 데이터가 아직 준비되지 않았습니다. 다른 약점을 선택해 보세요.")
        return

    st.markdown(f"### {exp['grammar_point_id']} ({exp['level']})")
    st.caption(f"RAG 설명 · {cached_badge(exp.get('cached', False))}")

    # ── LLM 가공 블록 (generated_explanation + examples) ──
    st.markdown("#### 🧠 AI 설명")
    st.write(exp.get("generated_explanation", ""))
    examples = exp.get("examples", [])
    if examples:
        st.markdown("**예문**")
        for ex in examples:
            jp, ko = split_example(ex)
            st.markdown(f"<div class='jp-text'>{jp}</div>", unsafe_allow_html=True)
            if ko:
                st.markdown(f"<div class='jp-sub'>{ko}</div>", unsafe_allow_html=True)

    # ── retrieval 원본 블록 (사실, 가공 없음) ──
    st.markdown("#### 🔎 검색된 근거 (DB 원본 chunk)")
    retrieved = exp.get("retrieved", {})
    point = retrieved.get("point_chunk")
    if point:
        st.markdown(
            f"<div class='jp-text'>{point.get('japanese_name', '')}</div>",
            unsafe_allow_html=True,
        )
        st.write(point.get("korean_meaning", ""))
        meta = " · ".join(
            str(point.get(k)) for k in ("l1", "l2") if point.get(k)
        )
        if meta:
            st.caption(meta)
    compares = retrieved.get("compare_chunks", [])
    if compares:
        st.markdown("**혼동 비교**")
        for c in compares:
            st.markdown(f"<div class='jp-text'>{c.get('pair_label', '')}</div>", unsafe_allow_html=True)
            st.caption(c.get("confusion_point", ""))


def _restart_button() -> None:
    if st.button("처음부터 다시"):
        _reset_to_intro()
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="JLPT 진단 데모", page_icon="🇯🇵")
    st.markdown(_JP_STYLE, unsafe_allow_html=True)
    st.title("🇯🇵 JLPT 진단 데모")
    st.caption("로그인 없이 바로 체험 · AI 백엔드 동작 가시화 데모")
    _init_state()

    stage = st.session_state["stage"]
    if stage == STAGE_INTRO:
        _render_intro()
    elif stage == STAGE_QUIZ:
        _render_quiz()
    elif stage == STAGE_RESULT:
        _render_result()


if __name__ == "__main__":
    main()
