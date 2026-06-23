"""진단 API (api_endpoints §6).

규칙 채점 진단 플로우 — 세션 시작 → 출제(정답 제외) → 답안(서버 채점) → 완료/결과.
설계: `04_router_validation_plan.md` (검증 V1~V6 / 세션 생명주기 started→in_progress→completed).

보안 불변식 (정빈님 flow):
- 출제 응답은 `ClientQuestion` 경유 → 정답(correct_choice) 미노출.
- 채점은 서버에서 `DiagnosticQuestion.correct_choice` 조회 (클라 입력 신뢰 금지, V5).
- `question_id`는 DB FK 없는 논리 참조 → 라우터가 존재·세션소속 검증 (V2/V3).
"""

from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.diagnostic import (
    DIAGNOSTIC_LEVELS,
    AnswerProgress,
    DiagnosticResultResponse,
    ExplanationPreviewResponse,
    QuestionsResponse,
    RetrievedBlock,
    StartDiagnosticRequest,
    StartDiagnosticResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    WeakGrammarPoint,
)
from src.db.models import (
    AnonymousSession,
    Chunk,
    DiagnosticAnswer,
    DiagnosticQuestion,
    DiagnosticSession,
)
from src.db.session import SessionLocal, get_session
from src.services.cache import DbLlmCache, LlmCache
from src.services.diagnostic.flow import fetch_questions, to_client_question
from src.services.diagnostic.leveling import diagnose_level
from src.services.diagnostic.scoring import GradedAnswer, aggregate_score, grade_answer
from src.services.learning.explanation import generate_explanation_from_chunks
from src.services.learning.retrieval import retrieve_for_point
from src.services.llm import LlmProvider, get_provider

router = APIRouter(tags=["diagnosis"])


# ── 인증 / 공통 조회 ──
async def require_anonymous_session(
    authorization: str = Header(..., description="Session {token}"),
    session: AsyncSession = Depends(get_session),
) -> AnonymousSession:
    """`Authorization: Session {token}` 검증 → 유효·미만료 익명 세션."""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "session" or not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session 토큰 형식 오류")
    anon = (
        await session.execute(
            select(AnonymousSession).where(AnonymousSession.session_token == token)
        )
    ).scalar_one_or_none()
    if anon is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "익명 세션 무효")
    if anon.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "익명 세션 만료")
    return anon


def _parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "세션을 찾을 수 없음") from exc


async def _owned_session(
    session: AsyncSession, diagnosis_session_id: str, anon: AnonymousSession
) -> DiagnosticSession:
    """세션 존재 + 소유(익명 일치) 검증 (V1 / C1)."""
    diag = (
        await session.execute(
            select(DiagnosticSession).where(
                DiagnosticSession.id == _parse_uuid(diagnosis_session_id)
            )
        )
    ).scalar_one_or_none()
    if diag is None or diag.anonymous_session_id != anon.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "세션을 찾을 수 없음")
    return diag


# ── §6-1 진단 세션 시작 ──
@router.post(
    "/sessions",
    response_model=StartDiagnosticResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_diagnosis(
    body: StartDiagnosticRequest,
    session: AsyncSession = Depends(get_session),
    anon: AnonymousSession = Depends(require_anonymous_session),
) -> StartDiagnosticResponse:
    questions = await fetch_questions(
        session, levels=list(DIAGNOSTIC_LEVELS), limit=100
    )
    if not questions:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "진단 문항 미적재"
        )
    diag = DiagnosticSession(
        anonymous_session_id=anon.id,
        mode=body.mode,
        max_score=len(questions),
        status="started",
    )
    session.add(diag)
    await session.commit()
    await session.refresh(diag)
    return StartDiagnosticResponse(
        diagnostic_session_id=str(diag.id),
        status=diag.status,
        max_score=diag.max_score,
        started_at=diag.started_at,
    )


# ── §6-2 출제 (정답 제외) ──
@router.get("/sessions/{diagnosis_session_id}/questions", response_model=QuestionsResponse)
async def get_questions(
    diagnosis_session_id: str,
    session: AsyncSession = Depends(get_session),
    anon: AnonymousSession = Depends(require_anonymous_session),
) -> QuestionsResponse:
    diag = await _owned_session(session, diagnosis_session_id, anon)
    if diag.status == "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, "완료된 진단 세션")
    questions = await fetch_questions(
        session, levels=list(DIAGNOSTIC_LEVELS), limit=100
    )
    return QuestionsResponse(
        diagnostic_session_id=str(diag.id),
        questions=[to_client_question(q) for q in questions],
    )


# ── §6-3 답안 제출 (서버 채점, (c) 검증) ──
@router.post(
    "/sessions/{diagnosis_session_id}/answers",
    response_model=SubmitAnswerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_answer(
    diagnosis_session_id: str,
    body: SubmitAnswerRequest,
    session: AsyncSession = Depends(get_session),
    anon: AnonymousSession = Depends(require_anonymous_session),
) -> SubmitAnswerResponse:
    diag = await _owned_session(session, diagnosis_session_id, anon)  # V1
    if diag.status == "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, "완료된 진단 세션")

    # V2: question_id가 diagnostic_questions에 존재
    question = (
        await session.execute(
            select(DiagnosticQuestion).where(
                DiagnosticQuestion.question_key == body.question_id
            )
        )
    ).scalar_one_or_none()
    if question is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "존재하지 않는 문항")
    # V3: 문항이 세션 출제 레벨 범위에 속함
    if question.level not in DIAGNOSTIC_LEVELS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "세션 범위 밖 문항")
    # V4: selected_choice가 문항 선택지 키에 존재
    # choices는 모델상 dict로 선언됐으나 실제 적재값은 [{"key","text"}] 리스트.
    choices = cast("list[dict[str, Any]]", question.choices)
    choice_keys = {c["key"] for c in choices}
    if body.selected_choice not in choice_keys:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "유효하지 않은 선택지")

    # V5: 정답은 서버에서 조회 (클라 입력 신뢰 금지)
    graded = grade_answer(
        question_key=question.question_key,
        grammar_point_id=question.grammar_point_id,
        level=question.level,
        selected_choice=body.selected_choice,
        correct_choice=question.correct_choice,
    )

    answer = DiagnosticAnswer(
        diagnostic_session_id=diag.id,
        question_id=graded.question_key,
        grammar_point_id=graded.grammar_point_id,
        selected_choice=graded.selected_choice,
        correct_choice=graded.correct_choice,
        is_correct=graded.is_correct,
        time_spent_sec=body.time_spent_sec,
    )
    session.add(answer)
    if diag.status == "started":
        diag.status = "in_progress"
    try:
        await session.commit()  # V6: UNIQUE(session, question) 위반 → 409
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "이미 제출된 문항"
        ) from exc
    await session.refresh(answer)

    answered = (
        await session.execute(
            select(func.count())
            .select_from(DiagnosticAnswer)
            .where(DiagnosticAnswer.diagnostic_session_id == diag.id)
        )
    ).scalar_one()
    return SubmitAnswerResponse(
        answer_id=str(answer.id),
        is_correct=graded.is_correct,
        progress=AnswerProgress(answered=answered, total=diag.max_score),
    )


# ── 결과 집계 (complete/result 공통) ──
async def _compute_result(
    session: AsyncSession, diag: DiagnosticSession
) -> tuple[str | None, int, list[WeakGrammarPoint], str | None]:
    rows = list(
        (
            await session.execute(
                select(DiagnosticAnswer).where(
                    DiagnosticAnswer.diagnostic_session_id == diag.id
                )
            )
        ).scalars()
    )
    level_rows = (
        await session.execute(
            select(DiagnosticQuestion.question_key, DiagnosticQuestion.level)
        )
    ).all()
    levels: dict[str, str] = {str(k): str(v) for k, v in level_rows}
    graded = [
        GradedAnswer(
            question_key=a.question_id,
            grammar_point_id=a.grammar_point_id,
            level=str(levels.get(a.question_id, "")),
            selected_choice=a.selected_choice,
            correct_choice=a.correct_choice,
            is_correct=a.is_correct,
        )
        for a in rows
    ]
    level = diagnose_level(graded)
    score, _ = aggregate_score(graded)

    # 약점: 오답 grammar_point_id (중복 제거·입력 순서 보존) + error_count·level.
    err_count = Counter(g.grammar_point_id for g in graded if not g.is_correct)
    gp_level = {g.grammar_point_id: g.level for g in graded}
    seen: set[str] = set()
    weak: list[WeakGrammarPoint] = []
    for g in graded:
        if not g.is_correct and g.grammar_point_id not in seen:
            seen.add(g.grammar_point_id)
            weak.append(
                WeakGrammarPoint(
                    grammar_point_id=g.grammar_point_id,
                    error_count=err_count[g.grammar_point_id],
                    level=gp_level[g.grammar_point_id],
                )
            )
    recommended = weak[0].grammar_point_id if weak else None
    return level, score, weak, recommended


# ── §6-4 완료 ──
@router.post(
    "/sessions/{diagnosis_session_id}/complete",
    response_model=DiagnosticResultResponse,
)
async def complete_diagnosis(
    diagnosis_session_id: str,
    session: AsyncSession = Depends(get_session),
    anon: AnonymousSession = Depends(require_anonymous_session),
) -> DiagnosticResultResponse:
    diag = await _owned_session(session, diagnosis_session_id, anon)  # C1
    if diag.status == "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 완료됨")  # C2
    answered = (
        await session.execute(
            select(func.count())
            .select_from(DiagnosticAnswer)
            .where(DiagnosticAnswer.diagnostic_session_id == diag.id)
        )
    ).scalar_one()
    if answered < diag.max_score:  # C3
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"미완료 답안 ({answered}/{diag.max_score})",
        )

    level, score, weak, recommended = await _compute_result(session, diag)
    now = datetime.now(timezone.utc)
    diag.diagnosed_level = level
    diag.score = score
    diag.status = "completed"
    diag.completed_at = now
    anon.diagnostic_completed_at = now
    await session.commit()

    return DiagnosticResultResponse(
        diagnostic_session_id=str(diag.id),
        diagnosed_level=level,
        score=score,
        max_score=diag.max_score,
        weak_grammar_points=weak,
        recommended_start_point=recommended,
        completed_at=now,
    )


# ── §6-5 결과 재조회 ──
@router.get(
    "/sessions/{diagnosis_session_id}/result",
    response_model=DiagnosticResultResponse,
)
async def get_result(
    diagnosis_session_id: str,
    session: AsyncSession = Depends(get_session),
    anon: AnonymousSession = Depends(require_anonymous_session),
) -> DiagnosticResultResponse:
    diag = await _owned_session(session, diagnosis_session_id, anon)
    if diag.status != "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, "아직 완료되지 않은 진단")
    level, score, weak, recommended = await _compute_result(session, diag)
    return DiagnosticResultResponse(
        diagnostic_session_id=str(diag.id),
        diagnosed_level=diag.diagnosed_level,
        score=diag.score if diag.score is not None else score,
        max_score=diag.max_score,
        weak_grammar_points=weak,
        recommended_start_point=recommended,
        completed_at=diag.completed_at,
    )


# ── explanation 프리뷰 의존성 (테스트에서 override 가능) ──
def get_llm_provider() -> LlmProvider:
    return get_provider()


def get_llm_cache() -> LlmCache:
    # 캐시는 비즈니스 트랜잭션과 분리된 전용 sessionmaker로 동작 (db_cache 설계).
    return DbLlmCache(SessionLocal)


# ── §8-3 explanation 프리뷰 (게스트 경로, 03 §2-3 3블록) ──
@router.get(
    "/sessions/{diagnosis_session_id}/explanation/{grammar_point_id}",
    response_model=ExplanationPreviewResponse,
)
async def explanation_preview(
    diagnosis_session_id: str,
    grammar_point_id: str,
    session: AsyncSession = Depends(get_session),
    anon: AnonymousSession = Depends(require_anonymous_session),
    provider: LlmProvider = Depends(get_llm_provider),
    cache: LlmCache = Depends(get_llm_cache),
) -> ExplanationPreviewResponse:
    """진단 게스트가 약점 문법 포인트의 RAG 설명을 미리본다 (P3 게스트 경로).

    retrieval 원본(`retrieved`)과 LLM 생성(`generated_explanation`/`examples`)을
    분리한 3블록 (03 §2-3). chunk 미적재 포인트(N4 등)는 404 → 하린 빈 상태 분기.
    """
    await _owned_session(session, diagnosis_session_id, anon)

    level = (
        await session.execute(
            select(Chunk.level).where(
                Chunk.grammar_point_id == grammar_point_id,
                Chunk.chunk_type == "point",
            )
        )
    ).scalar_one_or_none()
    if level is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "해당 문법 포인트 설명 미준비 (chunk 미적재)"
        )

    chunks = await retrieve_for_point(
        session, grammar_point_id=grammar_point_id, level=level
    )
    result = await generate_explanation_from_chunks(
        provider=provider,
        cache=cache,
        grammar_point_id=grammar_point_id,
        level=level,
        chunks=chunks,
    )
    # generated 텍스트는 {explanation, examples[]} JSON (explanation_v1.RESPONSE_FORMAT).
    try:
        parsed = json.loads(result.text)
        explanation_text = str(parsed.get("explanation", ""))
        examples = [str(e) for e in parsed.get("examples", [])]
    except (json.JSONDecodeError, AttributeError):
        explanation_text = result.text
        examples = []

    point_chunk = next((c.body for c in chunks if c.chunk_type == "point"), None)
    compare_chunks = [c.body for c in chunks if c.chunk_type == "compare"]
    return ExplanationPreviewResponse(
        grammar_point_id=grammar_point_id,
        level=str(level),
        retrieved=RetrievedBlock(
            point_chunk=point_chunk, compare_chunks=compare_chunks
        ),
        generated_explanation=explanation_text,
        examples=examples,
        cached=result.cached,
    )
