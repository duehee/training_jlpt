"""LLM 응답 캐시 모델 (database_schema.md §14 계승)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, CreatedAtMixin


class LlmResponseCache(CreatedAtMixin, Base):
    """LLM 응답 캐싱으로 API 비용 절감."""

    __tablename__ = "llm_response_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cache_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_usage: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (Index("idx_llm_cache_key", "cache_key"),)
