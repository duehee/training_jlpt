"""회원 학습 도메인 모델 (database_schema.md §5, §9~12 계승).

users / learning_sessions / learning_records / weak_points / last_session.
규약(D-8): grammar_point_id는 base 문법 포인트만 참조 (variant/compare ID 금지).
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    """로그인 사용자 기준 정보."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    current_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    target_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # 익명 진단 후 가입 추적 (순환 FK → use_alter)
    initial_diagnostic_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "diagnostic_sessions.id",
            use_alter=True,
            name="fk_users_initial_diagnostic_session_id_diagnostic_sessions",
        ),
        nullable=True,
    )


class LearningSession(Base):
    """로그인 이후 한 번의 문법 학습 흐름."""

    __tablename__ = "learning_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    grammar_point_id: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    explanation_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (Index("idx_learning_sessions_user", "user_id"),)


class LearningRecord(TimestampMixin, Base):
    """문법 포인트 단위 누적 학습 이력."""

    __tablename__ = "learning_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    grammar_point_id: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    correct_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    mastery_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False, server_default=text("0.0")
    )
    last_result: Mapped[str] = mapped_column(String(30), nullable=False)
    last_reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    next_review_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("user_id", "grammar_point_id", name="learning_record_user_gp"),
        Index("idx_learning_records_user_gp", "user_id", "grammar_point_id"),
        Index(
            "idx_learning_records_next_review",
            "next_review_at",
            postgresql_where=text("next_review_at IS NOT NULL"),
        ),
    )


class WeakPoint(Base):
    """로그인 사용자 기준 취약 문법 포인트 누적."""

    __tablename__ = "weak_points"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    grammar_point_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    error_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    # 컬럼명은 'metadata' (SQLAlchemy 예약어 충돌 회피 위해 속성명은 meta)
    meta: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    identified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        UniqueConstraint("user_id", "grammar_point_id", name="weak_point_user_gp"),
        Index("idx_weak_points_user_gp", "user_id", "grammar_point_id"),
        Index("idx_weak_points_user_error", "user_id", text("error_count DESC")),
    )


class LastSession(Base):
    """재방문 시 이어하기 상태. 사용자당 1건."""

    __tablename__ = "last_session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )
    learning_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_sessions.id"), nullable=False
    )
    grammar_point_id: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (Index("idx_last_session_user", "user_id"),)
