"""설명 생성 노드 단위 테스트 (DB/실 API 불필요).

핵심: 캐시 miss→hit 결정성 = `llm_cache_hit` 1.0의 단위 수준 증명.
같은 입력 2회차는 provider를 다시 호출하지 않고 캐시에서 반환해야 한다.
"""

import asyncio

import pytest

from src.shared.cache.memory import InMemoryLlmCache
from src.services.learning.explanation import generate_explanation_from_chunks
from src.domains.content.dto.response import RetrievedChunk
from src.shared.llm.fake import FakeProvider
from src.shared.prompts import explanation_v1

_CHUNKS = [
    RetrievedChunk(
        chunk_key="grammar_n5_001",
        chunk_type="point",
        body={"japanese_name": "は", "korean_meaning": "주제·대비 조사"},
    ),
    RetrievedChunk(
        chunk_key="compare_n5_001_002",
        chunk_type="compare",
        body={"pair_label": "は vs が"},
    ),
]


def _gen(provider: FakeProvider, cache: InMemoryLlmCache, version: int = 1):
    return asyncio.run(
        generate_explanation_from_chunks(
            provider=provider,
            cache=cache,
            grammar_point_id="grammar_n5_001",
            level="N5",
            chunks=_CHUNKS,
            explanation_version=version,
            model="gpt-4o-mini",
        )
    )


def test_miss_calls_provider_then_hit_does_not() -> None:
    provider = FakeProvider(default='{"explanation": "X", "examples": []}')
    cache = InMemoryLlmCache()

    first = _gen(provider, cache)
    assert first.cached is False
    assert provider.call_count == 1

    second = _gen(provider, cache)
    assert second.cached is True
    assert second.text == first.text
    assert second.cache_key == first.cache_key
    # 캐시 hit → provider 재호출 없음 (llm_cache_hit 결정성)
    assert provider.call_count == 1


def test_default_model_is_4o_mini_and_temperature_zero() -> None:
    provider = FakeProvider()
    cache = InMemoryLlmCache()
    _gen(provider, cache)
    assert provider.calls[0]["model"] == "gpt-4o-mini"
    assert provider.calls[0]["temperature"] == 0.0


def test_different_angle_uses_different_cache_entry() -> None:
    provider = FakeProvider()
    cache = InMemoryLlmCache()
    r1 = _gen(provider, cache, version=1)  # angle 1
    r2 = _gen(provider, cache, version=2)  # angle 2
    assert r1.cache_key != r2.cache_key
    assert r1.angle == 1
    assert r2.angle == 2
    assert provider.call_count == 2  # 각 angle은 별도 캐시 → 둘 다 miss


def test_empty_chunks_raises() -> None:
    provider = FakeProvider()
    cache = InMemoryLlmCache()
    with pytest.raises(LookupError):
        asyncio.run(
            generate_explanation_from_chunks(
                provider=provider,
                cache=cache,
                grammar_point_id="grammar_n5_001",
                level="N5",
                chunks=[],
            )
        )


def test_angle_for_version_cycles() -> None:
    assert explanation_v1.angle_for_version(1) == 1
    assert explanation_v1.angle_for_version(2) == 2
    assert explanation_v1.angle_for_version(3) == 3
    assert explanation_v1.angle_for_version(4) == 1
