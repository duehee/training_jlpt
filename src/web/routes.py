"""웹 SSR 라우터 (design_backend 시안 4 화면 + /login stub + /restart).

데이터는 같은 ASGI app 안에서 진단 라우트 핸들러를 in-process 직접 호출해 채운다
(httpx 우회 — 서버 채점/검증/레벨 판정/약점 도출 불변식 단일 출처 재사용).
진단 핸들러의 `HTTPException`은 여기서 잡아 SSR 리다이렉트/폴백으로 변환한다.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.quiz.controller import (
    complete_diagnosis,
    get_questions,
    get_result,
    start_diagnosis,
    submit_answer,
)
from src.db.models import AnonymousSession, Chunk
from src.db.session import get_session
from src.domains.quiz.dto.request import StartDiagnosticRequest, SubmitAnswerRequest
from src.domains.quiz.dto.response import ClientQuestion, DiagnosticResultResponse
from src.domains.quiz.service import get_selected_choice
from src.web import presenter
from src.domains.session.service import (
    clear_active_diagnostic,
    create_anonymous_session,
    resolve_anonymous_session,
    set_active_diagnostic,
)
from src.web.session import COOKIE_MAX_AGE, COOKIE_NAME
from src.web.templates import templates

router = APIRouter(tags=["web"])

_REDIRECT = status.HTTP_303_SEE_OTHER


def _base_ctx(**extra: Any) -> dict[str, Any]:
    """템플릿 공통 컨텍스트. 본 세션은 로그인 미이식 → user=None(게스트).

    `request`는 Starlette `TemplateResponse(request, name, context)` 1번 인자로 전달.
    """
    return {"user": None, **extra}


async def _ensure_active_diag(
    session: AsyncSession, anon: AnonymousSession
) -> str:
    """활성 진단 세션 id 반환. 없으면 start_diagnosis 로 신설 + 포인터 set."""
    if anon.active_diagnostic_session_id is not None:
        return str(anon.active_diagnostic_session_id)
    started = await start_diagnosis(
        body=StartDiagnosticRequest(mode="initial_assessment"),
        session=session,
        anon=anon,
    )
    await set_active_diagnostic(
        session, anon, uuid.UUID(started.diagnostic_session_id)
    )
    return started.diagnostic_session_id


async def _restore_selection(
    session: AsyncSession, diag_id: str, question: ClientQuestion
) -> int:
    """기존 제출 답안에서 해당 문항의 선택 인덱스 복원(재방문 표시). 없으면 -1.

    답안 조회는 quiz service에 위임(ORM 누수 제거) → web은 화면 인덱스 매핑만.
    """
    selected = await get_selected_choice(
        session,
        diagnostic_session_id=uuid.UUID(diag_id),
        question_key=question.question_id,
    )
    if selected is None:
        return -1
    for idx, choice in enumerate(question.choices):
        if choice.get("key") == selected:
            return idx
    return -1


async def _enrich_points(
    session: AsyncSession, grammar_point_ids: list[str]
) -> dict[str, dict[str, str | None]]:
    """약점 grammar_point_id → 표시명(jp/sub) enrich. chunks(point) body 조회.

    chunk 미적재(N4 등) 포인트는 결과 dict에서 누락 → presenter 폴백.
    """
    if not grammar_point_ids:
        return {}
    rows = (
        await session.execute(
            select(Chunk.grammar_point_id, Chunk.body).where(
                Chunk.grammar_point_id.in_(grammar_point_ids),
                Chunk.chunk_type == "point",
            )
        )
    ).all()
    enriched: dict[str, dict[str, str | None]] = {}
    for grammar_point_id, body in rows:
        if grammar_point_id is None or not isinstance(body, dict):
            continue
        enriched[str(grammar_point_id)] = {
            "jp": body.get("japanese_name"),
            "sub": body.get("korean_meaning"),
        }
    return enriched


# ── 화면 ──
@router.get("/", response_class=HTMLResponse)
async def intro(
    request: Request, session: AsyncSession = Depends(get_session)
) -> Response:
    """진단 소개(게스트 진입). 익명 세션 없으면 생성 + 쿠키 set."""
    anon = await resolve_anonymous_session(session, request.cookies.get(COOKIE_NAME))
    response = templates.TemplateResponse(request, "intro.html", _base_ctx())
    if anon is None:
        anon = await create_anonymous_session(session)
        response.set_cookie(
            COOKIE_NAME,
            anon.session_token,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
        )
    return response


@router.get("/quiz", response_class=HTMLResponse)
async def quiz(
    request: Request,
    i: int = 0,
    sel: int = -1,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """진단 문항 화면. 활성 진단 세션 보장 후 i번째 문항 렌더."""
    anon = await resolve_anonymous_session(session, request.cookies.get(COOKIE_NAME))
    if anon is None:
        return RedirectResponse("/", status_code=_REDIRECT)
    diag_id = await _ensure_active_diag(session, anon)
    try:
        questions = (
            await get_questions(
                diagnosis_session_id=diag_id, session=session, anon=anon
            )
        ).questions
    except HTTPException as exc:
        if exc.status_code == status.HTTP_409_CONFLICT:  # 완료된 세션 → 결과로
            return RedirectResponse("/result", status_code=_REDIRECT)
        raise
    total = len(questions)
    if total == 0:
        return HTMLResponse(
            "<p>진단 문항이 아직 준비되지 않았습니다.</p>", status_code=503
        )
    i = max(0, min(i, total - 1))
    question = questions[i]
    selected_idx = sel if sel >= 0 else await _restore_selection(
        session, diag_id, question
    )
    ctx = presenter.quiz_context(
        question, index=i, total=total, selected_idx=selected_idx
    )
    return templates.TemplateResponse(request, "quiz.html", _base_ctx(**ctx))


@router.get("/quiz/next")
async def quiz_next(
    request: Request,
    i: int,
    sel: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """선택 답안 저장 후 다음 문항 또는 채점으로 리다이렉트."""
    anon = await resolve_anonymous_session(session, request.cookies.get(COOKIE_NAME))
    if anon is None:
        return RedirectResponse("/", status_code=_REDIRECT)
    if anon.active_diagnostic_session_id is None:
        return RedirectResponse("/quiz", status_code=_REDIRECT)
    diag_id = str(anon.active_diagnostic_session_id)
    questions = (
        await get_questions(diagnosis_session_id=diag_id, session=session, anon=anon)
    ).questions
    total = len(questions)
    if 0 <= i < total:
        key = presenter.selected_choice_key(questions[i], sel)
        if key is not None:
            try:
                await submit_answer(
                    diagnosis_session_id=diag_id,
                    body=SubmitAnswerRequest(
                        question_id=questions[i].question_id, selected_choice=key
                    ),
                    session=session,
                    anon=anon,
                )
            except HTTPException as exc:
                # 409 = 이미 제출/완료된 문항 → Phase 1 선형 흐름에서는 무시.
                if exc.status_code != status.HTTP_409_CONFLICT:
                    raise
    if i < total - 1:
        return RedirectResponse(f"/quiz?i={i + 1}", status_code=_REDIRECT)
    return RedirectResponse("/scoring", status_code=_REDIRECT)


@router.get("/scoring", response_class=HTMLResponse)
async def scoring(request: Request) -> Response:
    """채점 로더(2초 meta refresh → /result). 정적."""
    return templates.TemplateResponse(request, "scoring.html", _base_ctx())


@router.get("/result", response_class=HTMLResponse)
async def result(
    request: Request, session: AsyncSession = Depends(get_session)
) -> Response:
    """진단 결과. 최초 진입은 complete, 재조회는 409→get_result 폴백."""
    anon = await resolve_anonymous_session(session, request.cookies.get(COOKIE_NAME))
    if anon is None or anon.active_diagnostic_session_id is None:
        return RedirectResponse("/", status_code=_REDIRECT)
    diag_id = str(anon.active_diagnostic_session_id)
    try:
        res: DiagnosticResultResponse = await complete_diagnosis(
            diagnosis_session_id=diag_id, session=session, anon=anon
        )
    except HTTPException as exc:
        if exc.status_code == status.HTTP_409_CONFLICT:  # 이미 완료 → 재조회
            res = await get_result(
                diagnosis_session_id=diag_id, session=session, anon=anon
            )
        elif exc.status_code == status.HTTP_400_BAD_REQUEST:  # 미완료 → 이어풀기
            return RedirectResponse("/quiz", status_code=_REDIRECT)
        else:
            raise

    enrich = await _enrich_points(
        session, [w.grammar_point_id for w in res.weak_grammar_points]
    )
    perfect = res.score == res.max_score
    rec_title, rec_body = presenter.recommendation(
        perfect, res.recommended_start_point, enrich
    )
    ctx = {
        "result_level": res.diagnosed_level or "판정 보류",
        "score_val": res.score,
        "score_total": res.max_score,
        "result_copy": presenter.result_copy(perfect, res.diagnosed_level),
        "perfect": perfect,
        "has_weak": not perfect,
        "weak_list": presenter.shape_weak_list(res.weak_grammar_points, enrich),
        "rec_title": rec_title,
        "rec_body": rec_body,
    }
    return templates.TemplateResponse(request, "result.html", _base_ctx(**ctx))


@router.get("/restart")
async def restart(
    request: Request, session: AsyncSession = Depends(get_session)
) -> Response:
    """진단 답안 초기화(활성 포인터 NULL) 후 intro로."""
    anon = await resolve_anonymous_session(session, request.cookies.get(COOKIE_NAME))
    if anon is not None:
        await clear_active_diagnostic(session, anon)
    return RedirectResponse("/", status_code=_REDIRECT)


def _stub_page(title: str, body: str, back_href: str, back_label: str) -> HTMLResponse:
    """미이식 화면용 plain HTMLResponse stub(200). 템플릿 영역 미접근."""
    return HTMLResponse(
        f"<!DOCTYPE html><html lang='ko'><head><meta charset='utf-8'>"
        f"<title>{title}</title></head>"
        f"<body style=\"font-family:sans-serif;max-width:480px;margin:80px auto;"
        f"padding:0 24px;text-align:center;color:#1a1c20\">"
        f"<h1 style='font-size:20px'>{title}</h1>"
        f"<p style='color:#757b86;font-size:14px;line-height:1.6'>{body}</p>"
        f"<p style='margin-top:24px'><a href='{back_href}' "
        f"style='color:#2f55d4;font-weight:700'>{back_label}</a></p>"
        f"</body></html>"
    )


@router.get("/login", response_class=HTMLResponse)
async def login_stub(request: Request) -> Response:
    """로그인 미이식 — base topbar 로그인 버튼 404 방지용 stub 200(정빈님 (가))."""
    return _stub_page(
        "로그인은 준비 중입니다",
        "다음 단계에서 로그인/회원가입이 추가됩니다.<br>지금은 게스트로 진단을 체험해 보세요.",
        "/",
        "← 진단 시작으로 돌아가기",
    )


@router.get("/explain/{point_id}", response_class=HTMLResponse)
async def explain_stub(request: Request, point_id: str) -> Response:
    """약점 문법 설명 미이식 — result 약점 카드 클릭 404 방지용 stub 200(정빈님 (가))."""
    return _stub_page(
        "문법 설명은 준비 중입니다",
        "이 약점 문법의 RAG 설명은 다음 단계에서 추가됩니다.<br>곧 검색 근거와 함께 풀이를 보여드릴게요.",
        "/result",
        "← 진단 결과로 돌아가기",
    )
