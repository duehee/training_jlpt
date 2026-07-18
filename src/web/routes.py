"""웹 SSR 라우터 (design_backend 시안 4 화면 + /login stub + /restart).

데이터는 같은 ASGI app 안에서 진단 라우트 핸들러를 in-process 직접 호출해 채운다
(httpx 우회 — 서버 채점/검증/레벨 판정/약점 도출 불변식 단일 출처 재사용).
진단 핸들러의 `HTTPException`은 여기서 잡아 SSR 리다이렉트/폴백으로 변환한다.
"""

from __future__ import annotations

import uuid
from typing import Any
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.quiz.controller import (
    complete_diagnosis,
    get_questions,
    get_result,
    start_diagnosis,
    submit_answer,
)
from src.db.models import AnonymousSession, User
from src.db.session import get_session
from src.domains.content.service import enrich_points
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
from src.core.config import settings
from src.domains.user.controller import login as auth_login
from src.domains.user.controller import resend_verification as auth_resend
from src.domains.user.controller import signup as auth_signup
from src.domains.user.dto.request import (
    LoginRequest,
    ResendVerificationRequest,
    SignupRequest,
)
from src.domains.user.service import (
    InvalidVerificationTokenError,
    VerificationTokenExpiredError,
    resolve_user_from_token,
    verify_email_token,
)
from src.shared.auth.email import EmailSender, get_email_sender
from src.web.session import ACCESS_COOKIE_NAME, COOKIE_MAX_AGE, COOKIE_NAME
from src.web.templates import templates

router = APIRouter(tags=["web"])

_REDIRECT = status.HTTP_303_SEE_OTHER


def _base_ctx(user: dict[str, str] | None = None, **extra: Any) -> dict[str, Any]:
    """템플릿 공통 컨텍스트. 로그인 사용자면 topbar user 주입(②=A 전 페이지 일관).

    `request`는 Starlette `TemplateResponse(request, name, context)` 1번 인자로 전달.
    """
    return {"user": user, **extra}


def _topbar_user(user: User | None) -> dict[str, str] | None:
    """로그인 User → topbar 표시용 최소 dict. 게스트(None)면 None.

    base.html topbar는 `user.initial`, dashboard는 `user.name`을 참조 → 둘 다 채운다.
    """
    if user is None:
        return None
    nickname = user.nickname
    return {
        "nickname": nickname,
        "name": nickname,
        "initial": (nickname[:1] or "U").upper(),
    }


async def _resolve_user(session: AsyncSession, request: Request) -> User | None:
    """access_token 쿠키 → 로그인 User. 없거나 무효면 None(게스트).

    쿠키 읽기는 web presentation, 토큰→User 해석은 domains/user(resolve_user_from_token).
    """
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not token:
        return None
    return await resolve_user_from_token(session, token)


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


# ── 화면 ──
@router.get("/", response_class=HTMLResponse)
async def intro(
    request: Request, session: AsyncSession = Depends(get_session)
) -> Response:
    """진단 소개(게스트 진입). 익명 세션 없으면 생성 + 쿠키 set."""
    anon = await resolve_anonymous_session(session, request.cookies.get(COOKIE_NAME))
    user = await _resolve_user(session, request)
    response = templates.TemplateResponse(
        request, "intro.html", _base_ctx(user=_topbar_user(user))
    )
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
    user = await _resolve_user(session, request)
    return templates.TemplateResponse(
        request, "quiz.html", _base_ctx(user=_topbar_user(user), **ctx)
    )


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
async def scoring(
    request: Request, session: AsyncSession = Depends(get_session)
) -> Response:
    """채점 로더(2초 meta refresh → /result). topbar 로그인 표시(②=A)."""
    user = await _resolve_user(session, request)
    return templates.TemplateResponse(
        request, "scoring.html", _base_ctx(user=_topbar_user(user))
    )


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

    enrich = await enrich_points(
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
    user = await _resolve_user(session, request)
    return templates.TemplateResponse(
        request, "result.html", _base_ctx(user=_topbar_user(user), **ctx)
    )


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


async def _form_data(request: Request) -> dict[str, str]:
    """urlencoded 폼 본문 파싱(python-multipart 미설치 → Starlette form() 우회).

    SSR 로그인/가입 폼은 application/x-www-form-urlencoded 단순 폼이라 표준 parse_qs로
    충분. 다중값은 첫 값만 취한다(단일 필드 폼). dep 추가 없이 web 계층에서 처리.
    """
    raw = (await request.body()).decode("utf-8")
    return {
        key: values[0]
        for key, values in parse_qs(raw, keep_blank_values=True).items()
    }


async def _render_login(
    request: Request,
    session: AsyncSession,
    mode: str,
    *,
    error: str | None = None,
    notice: str | None = None,
    unverified_email: str | None = None,
    form_email: str = "",
    form_name: str = "",
) -> Response:
    """login.html 렌더. mode 카피(presenter) + 상황별 슬롯 + topbar user 병합."""
    ctx = presenter.auth_context(mode)
    ctx.update(
        {
            "error": error,
            "notice": notice,
            "unverified_email": unverified_email,
            "form_email": form_email,
            "form_name": form_name,
            "google_enabled": bool(settings.google_client_id),
        }
    )
    user = await _resolve_user(session, request)
    return templates.TemplateResponse(
        request, "login.html", _base_ctx(user=_topbar_user(user), **ctx)
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    mode: str = "login",
    session: AsyncSession = Depends(get_session),
) -> Response:
    """로그인/회원가입 폼. 이미 로그인 상태면 마이페이지로."""
    if await _resolve_user(session, request) is not None:
        return RedirectResponse("/mypage", status_code=_REDIRECT)
    return await _render_login(request, session, mode)


@router.post("/login")
async def login_submit(
    request: Request,
    mode: str = "login",
    session: AsyncSession = Depends(get_session),
    sender: EmailSender = Depends(get_email_sender),
) -> Response:
    """로그인/회원가입 폼 제출. mode=signup 이면 가입, 아니면 로그인."""
    form = await _form_data(request)
    email = form.get("email", "").strip()
    password = form.get("password", "")
    if mode == "signup":
        name = form.get("name", "").strip()
        return await _submit_signup(request, session, sender, email, password, name)
    return await _submit_login(request, session, email, password)


async def _submit_signup(
    request: Request,
    session: AsyncSession,
    sender: EmailSender,
    email: str,
    password: str,
    name: str,
) -> Response:
    """회원가입 처리. 성공 시 확인 메일 안내 + 로그인 폼으로, 실패 시 에러 표시."""
    try:
        body = SignupRequest(email=email, password=password, nickname=name)
    except ValidationError:
        return await _render_login(
            request,
            session,
            "signup",
            error="이메일 형식과 이름(1~50자)을 확인해 주세요.",
            form_email=email,
            form_name=name,
        )
    try:
        await auth_signup(
            body=body,
            session=session,
            sender=sender,
            session_token=request.cookies.get(COOKIE_NAME),
        )
    except HTTPException as exc:
        # 409(이미 가입) → 로그인 유도, 그 외(400 비번정책 등) → 가입 폼 유지.
        target_mode = "login" if exc.status_code == status.HTTP_409_CONFLICT else "signup"
        return await _render_login(
            request,
            session,
            target_mode,
            error=str(exc.detail),
            form_email=email,
            form_name=name,
        )
    return await _render_login(
        request,
        session,
        "login",
        notice="메일의 링크를 눌러 이메일을 확인한 뒤 로그인해 주세요.",
        unverified_email=email,
        form_email=email,
    )


async def _submit_login(
    request: Request, session: AsyncSession, email: str, password: str
) -> Response:
    """로그인 처리. 성공 시 JWT 쿠키 set 후 마이페이지로, 실패 시 에러(403은 재발송 유도)."""
    try:
        result = await auth_login(
            body=LoginRequest(email=email, password=password), session=session
        )
    except HTTPException as exc:
        # 403 = 이메일 미확인 → 재발송 링크 노출(정빈님 UX: 엣지 복구 동선).
        unverified = email if exc.status_code == status.HTTP_403_FORBIDDEN else None
        return await _render_login(
            request,
            session,
            "login",
            error=str(exc.detail),
            unverified_email=unverified,
            form_email=email,
        )
    response = RedirectResponse("/mypage", status_code=_REDIRECT)
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        result.access_token,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        httponly=True,
        samesite="lax",
    )
    return response


async def _render_verify(
    request: Request,
    session: AsyncSession,
    status_key: str,
    *,
    email: str | None = None,
) -> Response:
    """verify.html 렌더. presenter 카피 + email 슬롯 + topbar user 병합."""
    ctx = presenter.verify_context(status_key)
    ctx["email"] = email
    user = await _resolve_user(session, request)
    return templates.TemplateResponse(
        request, "verify.html", _base_ctx(user=_topbar_user(user), **ctx)
    )


@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page(
    request: Request,
    token: str = "",
    session: AsyncSession = Depends(get_session),
) -> Response:
    """이메일 확인 링크(SSR). 토큰 소비 후 성공/만료/무효 결과 화면 렌더.

    메일의 확인 링크가 이 경로를 가리킨다(재현이 verify_url 연결). 성공 시 로그인 유도,
    만료/무효는 재발송 동선 제공(정빈님 UX: 엣지에서 막히지 않게).
    """
    if not token:
        return await _render_verify(request, session, "invalid")
    try:
        user = await verify_email_token(session, token)
    except VerificationTokenExpiredError:
        return await _render_verify(request, session, "expired")
    except InvalidVerificationTokenError:
        return await _render_verify(request, session, "invalid")
    return await _render_verify(request, session, "success", email=user.email)


@router.post("/login/resend")
async def login_resend(
    request: Request,
    session: AsyncSession = Depends(get_session),
    sender: EmailSender = Depends(get_email_sender),
) -> Response:
    """확인 메일 재발송. 계정 존재/상태와 무관하게 항상 동일 안내(비노출)."""
    email = (await _form_data(request)).get("email", "").strip()
    try:
        await auth_resend(
            body=ResendVerificationRequest(email=email), session=session, sender=sender
        )
    except (ValidationError, HTTPException):
        pass  # 재발송은 항상 동일 응답 — 실패도 동일 안내로 흡수.
    return await _render_login(
        request,
        session,
        "login",
        notice="확인 메일을 다시 보냈어요. 메일함(스팸함 포함)을 확인해 주세요.",
        form_email=email,
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
