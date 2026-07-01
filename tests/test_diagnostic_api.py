"""진단 API 라우터 통합 테스트 (실DB E2E).

기존 순수 단위 테스트와 달리 DB가 필요하다 — `diagnostic_questions`가 적재된
환경에서만 동작하고, 미가용 시 skip한다 (E-19 "동작 확인" 패턴). 생성 데이터는
테스트 종료 시 정리한다.

검증 축: 진단 생명주기(started→in_progress→completed) + (c) 검증(V2/V6) +
정답 비노출 불변식 + 인증.
"""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.api.main import app
from src.api.routes.diagnostic import get_llm_cache, get_llm_provider
from src.core.config import settings
from src.db.session import engine
from src.shared.cache.memory import InMemoryLlmCache
from src.shared.llm.fake import FakeProvider


def _diagnostic_questions_count() -> int:
    # 전역 engine은 테스트 본체(별도 asyncio.run 루프)에서 쓰므로, skip 체크는
    # 임시 engine으로 격리한다 (engine을 닫힌 루프에 바인딩하지 않도록).
    async def _q() -> int:
        eng = create_async_engine(settings.database_url)
        try:
            async with eng.connect() as conn:
                n = (
                    await conn.execute(
                        text("SELECT count(*) FROM diagnostic_questions")
                    )
                ).scalar()
            return int(n or 0)
        finally:
            await eng.dispose()

    try:
        return asyncio.run(_q())
    except Exception:
        return -1


pytestmark = pytest.mark.skipif(
    _diagnostic_questions_count() < 10,
    reason="DB 미가용 또는 diagnostic_questions 미적재 (통합 테스트 skip)",
)


async def _cleanup(token: str, diag_id: str | None) -> None:
    async with engine.begin() as conn:
        if diag_id is not None:
            await conn.execute(
                text(
                    "DELETE FROM diagnostic_answers "
                    "WHERE diagnostic_session_id = :d"
                ),
                {"d": diag_id},
            )
            await conn.execute(
                text("DELETE FROM diagnostic_sessions WHERE id = :d"), {"d": diag_id}
            )
        await conn.execute(
            text("DELETE FROM anonymous_sessions WHERE session_token = :t"),
            {"t": token},
        )


def test_diagnostic_flow_e2e() -> None:
    """전체 진단 플로우 + 검증 규칙 + 보안 불변식을 한 번에 확인."""

    async def flow() -> None:
        transport = ASGITransport(app=app)
        token = ""
        diag_id: str | None = None
        try:
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                # 익명 세션
                r = await client.post("/api/v1/sessions/anonymous")
                assert r.status_code == 201
                token = r.json()["session_token"]
                headers = {"Authorization": f"Session {token}"}

                # 진단 세션 시작
                r = await client.post(
                    "/api/v1/diagnosis/sessions",
                    json={"mode": "initial_assessment"},
                    headers=headers,
                )
                assert r.status_code == 201
                start = r.json()
                diag_id = start["diagnostic_session_id"]
                assert start["status"] == "started"
                assert start["max_score"] == 10

                # 출제 — 정답 비노출 불변식
                r = await client.get(
                    f"/api/v1/diagnosis/sessions/{diag_id}/questions",
                    headers=headers,
                )
                assert r.status_code == 200
                questions = r.json()["questions"]
                assert len(questions) == 10
                assert "correct_choice" not in r.text

                # 답안 10건 (전부 A)
                for q in questions:
                    r = await client.post(
                        f"/api/v1/diagnosis/sessions/{diag_id}/answers",
                        json={
                            "question_id": q["question_id"],
                            "selected_choice": "A",
                            "time_spent_sec": 5,
                        },
                        headers=headers,
                    )
                    assert r.status_code == 201, r.text
                assert r.json()["progress"] == {"answered": 10, "total": 10}

                # V6: 중복 제출 409
                r = await client.post(
                    f"/api/v1/diagnosis/sessions/{diag_id}/answers",
                    json={"question_id": questions[0]["question_id"], "selected_choice": "A"},
                    headers=headers,
                )
                assert r.status_code == 409

                # V2: 존재하지 않는 문항 400
                r = await client.post(
                    f"/api/v1/diagnosis/sessions/{diag_id}/answers",
                    json={"question_id": "q_zzz_999", "selected_choice": "A"},
                    headers=headers,
                )
                assert r.status_code == 400

                # 완료
                r = await client.post(
                    f"/api/v1/diagnosis/sessions/{diag_id}/complete", headers=headers
                )
                assert r.status_code == 200
                result = r.json()
                assert result["max_score"] == 10
                # 전부 A → 정답 분포상 정답 2건(A×2), 오답 8건 → weak 8.
                assert result["score"] == 2
                assert len(result["weak_grammar_points"]) == 8
                assert result["recommended_start_point"] is not None

                # C2: 재완료 409
                r = await client.post(
                    f"/api/v1/diagnosis/sessions/{diag_id}/complete", headers=headers
                )
                assert r.status_code == 409

                # 결과 재조회 — 동일 구조
                r = await client.get(
                    f"/api/v1/diagnosis/sessions/{diag_id}/result", headers=headers
                )
                assert r.status_code == 200
                assert r.json()["score"] == 2

                # 인증 실패 401
                r = await client.post(
                    "/api/v1/diagnosis/sessions",
                    json={"mode": "x"},
                    headers={"Authorization": "Session invalid"},
                )
                assert r.status_code == 401
        finally:
            await _cleanup(token, diag_id)
            # 전역 engine 풀을 이 루프에 남기지 않는다 (후속 테스트 격리).
            await engine.dispose()

    asyncio.run(flow())


def test_explanation_preview() -> None:
    """게스트 explanation 프리뷰 — 3블록 구조 + 캐시 miss→hit + N4 빈 상태(404).

    실 OpenAI 비용을 피하려 provider/cache를 FakeProvider + InMemoryLlmCache로
    override한다 (DI 경로 검증). 03 §2-3 retrieved/generated/cached 분리 확인.
    """

    shared_cache = InMemoryLlmCache()
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider()
    app.dependency_overrides[get_llm_cache] = lambda: shared_cache

    async def flow() -> None:
        transport = ASGITransport(app=app)
        token = ""
        diag_id: str | None = None
        try:
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                r = await client.post("/api/v1/sessions/anonymous")
                token = r.json()["session_token"]
                headers = {"Authorization": f"Session {token}"}
                r = await client.post(
                    "/api/v1/diagnosis/sessions",
                    json={"mode": "initial_assessment"},
                    headers=headers,
                )
                diag_id = r.json()["diagnostic_session_id"]

                # N5 적재 포인트 → 200, 3블록, 캐시 miss(첫 호출)
                url = (
                    f"/api/v1/diagnosis/sessions/{diag_id}"
                    "/explanation/grammar_n5_002"
                )
                r = await client.get(url, headers=headers)
                assert r.status_code == 200, r.text
                body = r.json()
                assert body["grammar_point_id"] == "grammar_n5_002"
                assert body["level"] == "N5"
                assert body["retrieved"]["point_chunk"] is not None
                assert body["generated_explanation"] == "FAKE"
                assert body["cached"] is False

                # 동일 요청 재호출 → 캐시 hit
                r = await client.get(url, headers=headers)
                assert r.status_code == 200
                assert r.json()["cached"] is True

                # N4 미적재 포인트 → 404 (하린 빈 상태 분기)
                r = await client.get(
                    f"/api/v1/diagnosis/sessions/{diag_id}"
                    "/explanation/grammar_n4_058",
                    headers=headers,
                )
                assert r.status_code == 404
        finally:
            await _cleanup(token, diag_id)
            await engine.dispose()

    try:
        asyncio.run(flow())
    finally:
        app.dependency_overrides.pop(get_llm_provider, None)
        app.dependency_overrides.pop(get_llm_cache, None)
