"""컨텐트(content) 서비스 — 문법 청크·비교쌍 조회 (async, ORM).

RAG 검색(retrieve) + 표시명 enrich + 포인트 레벨 조회. content는 외부 API가 없고,
다른 도메인(learning 설명, quiz explanation preview, web 약점 enrich)이 가져다 쓴다.
"""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Chunk, ComparisonPair
from src.domains.content.dto.response import RetrievedChunk


async def retrieve_for_point(
    session: AsyncSession,
    *,
    grammar_point_id: str,
    level: str,
    include_compare: bool = True,
) -> list[RetrievedChunk]:
    """포인트 + 관련 compare 청크를 반환. point 우선, 그다음 compare(키 정렬)."""
    point_stmt = select(Chunk).where(
        Chunk.grammar_point_id == grammar_point_id,
        Chunk.chunk_type == "point",
        Chunk.level == level,
    )
    point_chunks = list((await session.execute(point_stmt)).scalars().all())

    results: list[RetrievedChunk] = [
        RetrievedChunk(chunk_key=c.chunk_key, chunk_type=c.chunk_type, body=c.body)
        for c in point_chunks
    ]

    if include_compare:
        pair_stmt = select(ComparisonPair.compare_id).where(
            ComparisonPair.level == level,
            or_(
                ComparisonPair.left_point_id == grammar_point_id,
                ComparisonPair.right_point_id == grammar_point_id,
            ),
        )
        compare_ids = [
            str(r) for r in (await session.execute(pair_stmt)).scalars().all()
        ]
        if compare_ids:
            # compare_id == 해당 compare 청크의 chunk_key (00_db_overview §4-2).
            cmp_stmt = (
                select(Chunk)
                .where(
                    Chunk.chunk_key.in_(compare_ids),
                    Chunk.chunk_type == "compare",
                )
                .order_by(Chunk.chunk_key)
            )
            for c in (await session.execute(cmp_stmt)).scalars().all():
                results.append(
                    RetrievedChunk(
                        chunk_key=c.chunk_key, chunk_type=c.chunk_type, body=c.body
                    )
                )

    return results


async def get_point_level(session: AsyncSession, grammar_point_id: str) -> str | None:
    """포인트 청크의 레벨. 미적재면 None (explanation preview 빈 상태 분기)."""
    return (
        await session.execute(
            select(Chunk.level).where(
                Chunk.grammar_point_id == grammar_point_id,
                Chunk.chunk_type == "point",
            )
        )
    ).scalar_one_or_none()


async def enrich_points(
    session: AsyncSession, grammar_point_ids: list[str]
) -> dict[str, dict[str, str | None]]:
    """약점 grammar_point_id → 표시명(jp/sub) enrich. chunks(point) body 조회.

    chunk 미적재(N4 등) 포인트는 결과 dict에서 누락 → 호출측(presenter) 폴백.
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
