"""콘텐츠 도메인 모델 — 재설계 핵심.

- `Chunk`: point / compare / variant 청크를 담는 단일 retrieval 테이블.
- `ComparisonPair`: 비교쌍 트리거 seed (cluster/star/left/right 단일 진실).

설계 근거: `docs/planning/session_4/be_jaehyeon/04_target_db_design.md`.
- level을 1급 차원으로 두어 N1~N5 공통 (레벨 하드코딩 0).
- 표현 레이어(xlsx)의 지저분함은 어댑터가 흡수, DB는 깨끗한 값만 보유.
"""

import uuid
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Index,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, TimestampMixin

# 청크 타입 / 레벨 허용값 (앱·DB 양쪽 검증의 단일 출처)
CHUNK_TYPES: tuple[str, ...] = ("point", "compare", "variant")
LEVELS: tuple[str, ...] = ("N1", "N2", "N3", "N4", "N5")


class Chunk(TimestampMixin, Base):
    """point / compare / variant 통합 retrieval 청크."""

    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    # 사람이 읽는 식별자: grammar_n5_001 / compare_n5_001_002 / grammar_n5_026_informal
    chunk_key: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    level: Mapped[str] = mapped_column(String(4), nullable=False)
    chunk_type: Mapped[str] = mapped_column(String(16), nullable=False)
    # point/variant = 자기 base point id, compare = NULL
    grammar_point_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    # variant → base point, point/compare = NULL
    base_point_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    # TRUE / FALSE / 미평가(NULL)
    border_flag: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    body: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    l3_tags: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    border_meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    embedding_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    source_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="draft"
    )

    __table_args__ = (
        CheckConstraint(
            "chunk_type IN ('point','compare','variant')", name="chunk_type"
        ),
        CheckConstraint(
            "level IN ('N1','N2','N3','N4','N5')", name="level"
        ),
        Index("idx_chunks_level", "level"),
        Index("idx_chunks_type", "chunk_type"),
        Index("idx_chunks_level_type", "level", "chunk_type"),
        Index("idx_chunks_grammar_point", "grammar_point_id"),
        Index(
            "idx_chunks_border",
            "border_flag",
            postgresql_where=text("border_flag = TRUE"),
        ),
    )


class ComparisonPair(TimestampMixin, Base):
    """비교쌍 트리거 seed. cluster/star/left/right의 단일 진실.

    자기 대조(031_031i / 084_084i / 106_ta)는 left==right를 허용한다.
    ⚠️ left != right CHECK 제약을 추가하지 말 것.
    """

    __tablename__ = "comparison_pairs"

    compare_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    level: Mapped[str] = mapped_column(String(4), nullable=False)
    left_point_id: Mapped[str] = mapped_column(String(60), nullable=False)
    right_point_id: Mapped[str] = mapped_column(String(60), nullable=False)
    cluster: Mapped[str] = mapped_column(String(4), nullable=False)
    # 1 / 2 / 3 (어댑터가 "3star" → 3 으로 정규화)
    star_weight: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    confusion_point: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        CheckConstraint("star_weight BETWEEN 1 AND 3", name="star_weight"),
        Index("idx_cmp_pairs_level", "level"),
        Index("idx_cmp_pairs_points", "left_point_id", "right_point_id"),
    )
