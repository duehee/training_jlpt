"""InMemoryLlmCache 단위 테스트 (DB 불필요)."""

import asyncio

from src.services.cache.base import LlmCache
from src.services.cache.memory import InMemoryLlmCache


def test_memory_cache_satisfies_protocol() -> None:
    assert isinstance(InMemoryLlmCache(), LlmCache)


def test_memory_cache_miss_then_hit() -> None:
    cache = InMemoryLlmCache()

    async def scenario() -> tuple[str | None, str | None]:
        miss = await cache.get("k")
        await cache.set("k", model="m", prompt_hash="h", response_text="v")
        hit = await cache.get("k")
        return miss, hit

    miss, hit = asyncio.run(scenario())
    assert miss is None
    assert hit == "v"


def test_memory_cache_expired_entry_returns_none() -> None:
    cache = InMemoryLlmCache()

    async def scenario() -> str | None:
        await cache.set(
            "k", model="m", prompt_hash="h", response_text="v", ttl_seconds=-1
        )
        return await cache.get("k")

    assert asyncio.run(scenario()) is None
