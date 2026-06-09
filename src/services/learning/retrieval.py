"""학습 포인트 retrieval (RAG의 검색 단계).

설명 슬라이스(Stage 1)의 retrieval은 "알려진 포인트"에 대한 결정적 조회다:
- point 청크: grammar_point_id + chunk_type='point' + level
- 관련 compare 청크: comparison_pairs에서 이 포인트를 참조하는 쌍 → compare_id == chunk_key

벡터 유사도 검색(자연어 질의 → top-k)은 세션 4에서 실동작 확인됐고, 추천/탐색
시나리오에서 별도로 쓴다. 설명 생성은 포인트가 이미 정해져 있으므로 필터 조회가
더 정확·저렴하다 (06_rag_flow §7 "필터 결합" 권고).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Chunk, ComparisonPair


class RetrievedChunk(BaseModel):
    """retrieval 결과 1건 (프롬프트·캐시 키 입력)."""

    chunk_key: str
    chunk_type: str
    body: dict[str, Any]


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
        compare_ids = [str(r) for r in (await session.execute(pair_stmt)).scalars().all()]
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
