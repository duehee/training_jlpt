"""chunks.embedding_text → 벡터 임베딩 (OpenAI text-embedding-3-small).

사용법:
    poetry run python scripts/embed_chunks.py --level N5

`embedding`이 비어 있고 `embedding_text`가 있는 청크만 임베딩한다 (멱등 — 재실행 안전).
embedding_text가 바뀐 행을 다시 임베딩하려면 해당 행의 embedding을 NULL로 비우고 재실행.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from collections.abc import Iterator, Sequence
from typing import TypeVar

from openai import AsyncOpenAI
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings  # noqa: E402
from src.db.models import Chunk  # noqa: E402

T = TypeVar("T")


def batched(items: Sequence[T], size: int) -> Iterator[Sequence[T]]:
    """시퀀스를 size 단위로 분할."""
    for i in range(0, len(items), size):
        yield items[i : i + size]


async def embed_pending(level: str | None = None, batch_size: int = 100) -> int:
    """embedding이 NULL인 청크를 배치 임베딩하고 UPDATE. 처리 건수 반환."""
    if not settings.openai_api_key:
        raise SystemExit("OPENAI_API_KEY 미설정 — .env 확인")

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    updated = 0
    async with factory() as session:
        stmt = select(Chunk.chunk_key, Chunk.embedding_text).where(
            Chunk.embedding.is_(None),
            Chunk.embedding_text != "",
        )
        if level:
            stmt = stmt.where(Chunk.level == level)
        rows = (await session.execute(stmt)).all()

        for group in batched(rows, batch_size):
            keys = [r[0] for r in group]
            texts = [r[1] for r in group]
            resp = await client.embeddings.create(
                model=settings.embedding_model, input=texts
            )
            for key, item in zip(keys, resp.data):
                await session.execute(
                    update(Chunk)
                    .where(Chunk.chunk_key == key)
                    .values(embedding=item.embedding)
                )
                updated += 1
        await session.commit()

    await engine.dispose()
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="chunks 임베딩 (레벨 일반화)")
    parser.add_argument("--level", default=None, help="N5 / N4 / ... (미지정 시 전체)")
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()

    level = args.level.upper() if args.level else None
    count = asyncio.run(embed_pending(level, args.batch_size))
    print(f"임베딩 완료: {count} 청크 (model={settings.embedding_model})")


if __name__ == "__main__":
    main()
