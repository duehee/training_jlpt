"""웹 SSR 라우터 통합 테스트 (실DB E2E).

`test_diagnostic_api.py` 패턴 계승 — `diagnostic_questions` 적재 환경에서만 동작,
미가용 시 skip(E-19). 검증 축: intro→quiz→scoring→result 1 사이클 클릭 통과 +
쿠키 세션 + (B) FK 활성 포인터 + /login stub + /restart. 생성 데이터는 정리한다.

전역 engine(풀) 대신 NullPool 테스트 engine을 `get_session` 의존성 override로 주입한다
— asyncio.run 루프 종료 후 asyncpg가 닫힌 루프에서 graceful close를 시도해
RuntimeError 나는 것을 피하기 위함(연결을 풀에 남기지 않음).
"""

import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.api.main import app
from src.core.config import settings
from src.db.session import get_session
from src.web.session import COOKIE_NAME


def _diagnostic_questions_count() -> int:
    async def _q() -> int:
        eng = create_async_engine(settings.database_url, poolclass=NullPool)
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


def _override_get_session(engine: AsyncEngine) -> None:
    """앱의 get_session 의존성을 NullPool 테스트 engine 세션으로 교체."""
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _dep() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _dep


async def _cleanup(engine: AsyncEngine, token: str) -> None:
    """익명 세션 토큰 기준 생성된 진단 세션/답안/익명 세션 전부 삭제."""
    async with engine.begin() as conn:
        anon_id = (
            await conn.execute(
                text("SELECT id FROM anonymous_sessions WHERE session_token = :t"),
                {"t": token},
            )
        ).scalar()
        if anon_id is None:
            return
        diag_ids = [
            row[0]
            for row in (
                await conn.execute(
                    text(
                        "SELECT id FROM diagnostic_sessions "
                        "WHERE anonymous_session_id = :a"
                    ),
                    {"a": anon_id},
                )
            ).all()
        ]
        # 포인터 먼저 NULL → 진단 세션 삭제 시 FK 안전(ondelete=SET NULL도 보장)
        await conn.execute(
            text(
                "UPDATE anonymous_sessions "
                "SET active_diagnostic_session_id = NULL WHERE id = :a"
            ),
            {"a": anon_id},
        )
        for diag_id in diag_ids:
            await conn.execute(
                text(
                    "DELETE FROM diagnostic_answers WHERE diagnostic_session_id = :d"
                ),
                {"d": diag_id},
            )
            await conn.execute(
                text("DELETE FROM diagnostic_sessions WHERE id = :d"), {"d": diag_id}
            )
        await conn.execute(
            text("DELETE FROM anonymous_sessions WHERE id = :a"), {"a": anon_id}
        )


def test_web_full_cycle() -> None:
    """intro → quiz → (10문항) → scoring → result 1 사이클 + login + restart."""

    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        transport = ASGITransport(app=app)
        token = ""
        try:
            async with AsyncClient(
                transport=transport, base_url="http://test", follow_redirects=True
            ) as client:
                # intro — 익명 세션 쿠키 발급
                r = await client.get("/")
                assert r.status_code == 200
                token = client.cookies.get(COOKIE_NAME) or ""
                assert token.startswith("sess_")

                # quiz 진입 — 활성 진단 세션 신설
                r = await client.get("/quiz")
                assert r.status_code == 200
                assert "문항 1 /" in r.text

                # 10문항 선택(A) 제출 → 마지막은 scoring 으로
                for i in range(10):
                    r = await client.get(f"/quiz/next?i={i}&sel=0")
                    assert r.status_code == 200

                # scoring 로더
                r = await client.get("/scoring")
                assert r.status_code == 200
                assert "채점 중" in r.text

                # result — complete 경유 결과
                r = await client.get("/result")
                assert r.status_code == 200
                assert "진단 결과" in r.text
                assert "/ 10" in r.text

                # result 재조회(complete 409 → get_result 폴백) 도 200
                r = await client.get("/result")
                assert r.status_code == 200

                # login 폼 (실 이식) — 로그인/회원가입 전환 링크 노출
                r = await client.get("/login")
                assert r.status_code == 200
                assert "로그인" in r.text
                assert "회원가입" in r.text

                # explain stub (약점 카드 클릭 404 방지)
                r = await client.get("/explain/grammar_n5_001")
                assert r.status_code == 200
                assert "준비 중" in r.text

                # restart → intro 로, 활성 포인터 해제
                r = await client.get("/restart")
                assert r.status_code == 200
                assert r.url.path == "/"

                # restart 후 quiz 재진입 → 새 진단 세션(1문항부터)
                r = await client.get("/quiz")
                assert r.status_code == 200
                assert "문항 1 /" in r.text
        finally:
            app.dependency_overrides.pop(get_session, None)
            if token:
                await _cleanup(engine, token)
            await engine.dispose()

    asyncio.run(flow())


def test_quiz_without_cookie_redirects_to_intro() -> None:
    """쿠키 없이 /quiz 직접 진입 → intro 로 리다이렉트(가드)."""

    async def flow() -> None:
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        _override_get_session(engine)
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(
                transport=transport, base_url="http://test", follow_redirects=False
            ) as client:
                r = await client.get("/quiz")
                assert r.status_code == 303
                assert r.headers["location"] == "/"
        finally:
            app.dependency_overrides.pop(get_session, None)
            await engine.dispose()

    asyncio.run(flow())
