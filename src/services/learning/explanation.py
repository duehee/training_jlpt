"""설명 생성 노드 (캐시 경유 LLM 호출).

구조 (plan §2-6, 테스트 용이성):
- `generate_explanation_from_chunks`: DB 무관 순수 노드 — chunks를 받아 캐시→LLM.
  단위 테스트가 FakeProvider + InMemoryLlmCache로 miss→hit 결정성을 검증한다.
- `generate_explanation`: 위 노드 + DB retrieval 래퍼 (런타임 진입점).

정책: 기본 모델 gpt-4o-mini, temperature=0(결정성), 캐시 필수 경유.
"""

from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.services.cache.base import LlmCache, make_cache_key, make_prompt_hash
from src.services.learning.retrieval import RetrievedChunk, retrieve_for_point
from src.services.llm.base import LlmProvider
from src.services.prompts import explanation_v1


class ExplanationResult(BaseModel):
    """설명 생성 결과."""

    text: str  # JSON 문자열 ({explanation, examples[]})
    cached: bool
    model: str
    cache_key: str
    angle: int
    chunk_keys: list[str]


async def generate_explanation_from_chunks(
    *,
    provider: LlmProvider,
    cache: LlmCache,
    grammar_point_id: str,
    level: str,
    chunks: list[RetrievedChunk],
    explanation_version: int = 1,
    model: str | None = None,
) -> ExplanationResult:
    """chunks 근거로 설명 생성 (캐시 경유). DB 무관 — 단위 테스트 가능."""
    if not chunks:
        raise LookupError(
            f"근거 청크 없음: grammar_point_id={grammar_point_id} level={level}"
        )

    model = model or settings.openai_chat_model
    angle = explanation_v1.angle_for_version(explanation_version)
    chunk_keys = sorted(c.chunk_key for c in chunks)

    prompt_hash = make_prompt_hash(
        {
            "task": "explanation",
            "grammar_point_id": grammar_point_id,
            "level": level,
            "chunk_keys": chunk_keys,
            "angle": angle,
            "template_version": explanation_v1.TEMPLATE_VERSION,
        }
    )
    cache_key = make_cache_key(model, prompt_hash)

    cached = await cache.get(cache_key)
    if cached is not None:
        return ExplanationResult(
            text=cached,
            cached=True,
            model=model,
            cache_key=cache_key,
            angle=angle,
            chunk_keys=chunk_keys,
        )

    messages = explanation_v1.build_messages(
        grammar_point_id=grammar_point_id,
        level=level,
        chunks=[c.model_dump() for c in chunks],
        angle=angle,
    )
    result = await provider.chat(
        messages,
        model=model,
        temperature=0.0,
        response_format=explanation_v1.RESPONSE_FORMAT,
    )
    await cache.set(
        cache_key,
        model=model,
        prompt_hash=prompt_hash,
        response_text=result.text,
        token_usage={
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
        },
    )
    return ExplanationResult(
        text=result.text,
        cached=False,
        model=model,
        cache_key=cache_key,
        angle=angle,
        chunk_keys=chunk_keys,
    )


async def generate_explanation(
    session: AsyncSession,
    *,
    provider: LlmProvider,
    cache: LlmCache,
    grammar_point_id: str,
    level: str,
    explanation_version: int = 1,
    model: str | None = None,
) -> ExplanationResult:
    """런타임 진입점: DB retrieval → 설명 생성 (캐시 경유)."""
    chunks = await retrieve_for_point(
        session, grammar_point_id=grammar_point_id, level=level
    )
    return await generate_explanation_from_chunks(
        provider=provider,
        cache=cache,
        grammar_point_id=grammar_point_id,
        level=level,
        chunks=chunks,
        explanation_version=explanation_version,
        model=model,
    )
