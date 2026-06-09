"""Stage 1 설명 슬라이스 end-to-end 데모 (실 DB).

흐름: 포인트 1개 → DB retrieval(point + 관련 compare) → LLM 설명 생성 → DB 캐시
저장 → 같은 입력 2회차 캐시 hit 확인.

사용법:
    poetry run python scripts/demo_explanation.py --point grammar_n5_001 --level N5

OPENAI_API_KEY 가 있으면 실제 gpt-4o-mini 호출, 없으면 FakeProvider로 흐름만 시연.
실 DB(chunks 적재됨)가 필요하다.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings  # noqa: E402
from src.services.cache.db_cache import DbLlmCache  # noqa: E402
from src.services.learning.explanation import generate_explanation  # noqa: E402
from src.services.llm.base import LlmProvider  # noqa: E402
from src.services.llm.fake import FakeProvider  # noqa: E402
from src.services.llm.openai_provider import OpenAIProvider  # noqa: E402


async def run(grammar_point_id: str, level: str) -> None:
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    provider: LlmProvider
    if settings.openai_api_key:
        provider = OpenAIProvider(settings.openai_api_key)
        print(f"provider = OpenAIProvider (model={settings.openai_chat_model})")
    else:
        provider = FakeProvider()
        print("provider = FakeProvider (OPENAI_API_KEY 미설정 — 흐름만 시연)")

    cache = DbLlmCache(factory)

    async with factory() as session:
        # 1회차 — 캐시 miss → LLM 호출 → DB 저장
        first = await generate_explanation(
            session,
            provider=provider,
            cache=cache,
            grammar_point_id=grammar_point_id,
            level=level,
        )
        print(f"\n[1회차] cached={first.cached} angle={first.angle}")
        print(f"  chunk_keys={first.chunk_keys}")
        print(f"  cache_key={first.cache_key}")
        print(f"  text={first.text[:200]}...")

        # 2회차 — 같은 입력 → 캐시 hit (LLM 미호출)
        second = await generate_explanation(
            session,
            provider=provider,
            cache=cache,
            grammar_point_id=grammar_point_id,
            level=level,
        )
        print(f"\n[2회차] cached={second.cached} (hit 기대=True)")
        print(f"  동일 cache_key={second.cache_key == first.cache_key}")
        print(f"  동일 text={second.text == first.text}")

    await engine.dispose()

    ok = (not first.cached) and second.cached and second.text == first.text
    print(f"\n=== Stage 1 e2e {'PASS' if ok else 'CHECK'} ===")


def main() -> None:
    parser = argparse.ArgumentParser(description="설명 슬라이스 e2e 데모")
    parser.add_argument("--point", default="grammar_n5_001")
    parser.add_argument("--level", default="N5")
    args = parser.parse_args()
    asyncio.run(run(args.point, args.level))


if __name__ == "__main__":
    main()
