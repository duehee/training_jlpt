"""익명 진단 도메인 모델 (database_schema.md §6~8 계승 + diagnostic_questions 신설).

익명 구간: anonymous_sessions / diagnostic_sessions / diagnostic_answers.
신설(D-6): diagnostic_questions (진단 문제 seed의 DB 테이블화).
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, CreatedAtMixin, TimestampMixin


class AnonymousSession(TimestampMixin, Base):
    """비로그인 사용자의 진단 흐름 임시 상태."""

    __tablename__ = "anonymous_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    session_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    # 로그인 후 연결 (순환 FK → use_alter)
    linked_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            use_alter=True,
            name="fk_anonymous_sessions_linked_user_id_users",
        ),
        nullable=True,
    )
    diagnostic_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    # (B) 쿠키→DB 1홉 해소용 활성 진단 세션 포인터 (순환 FK → use_alter).
    # diag 삭제 시 포인터 자동 NULL (ondelete=SET NULL) → cleanup/restart 정합.
    active_diagnostic_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "diagnostic_sessions.id",
            use_alter=True,
            ondelete="SET NULL",
            # Postgres 식별자 63자 한도 회피 위해 축약 (idx 명칭과 일관).
            name="fk_anon_sessions_active_diag_session_id",
        ),
        nullable=True,
    )

    __table_args__ = (
        Index("idx_anon_sessions_linked_user", "linked_user_id"),
        Index("idx_anon_sessions_active_diag", "active_diagnostic_session_id"),
    )


class DiagnosticSession(Base):
    """익명 사용자의 한 번의 진단 흐름. user_id를 두지 않음(익명 전용)."""

    __tablename__ = "diagnostic_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    anonymous_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("anonymous_sessions.id"),
        nullable=False,
    )
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    diagnosed_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (Index("idx_diag_sessions_anon", "anonymous_session_id"),)


class DiagnosticQuestion(TimestampMixin, Base):
    """진단 문제 seed (D-6 신설). diagnostic_answers.question_id가 question_key를 참조."""

    __tablename__ = "diagnostic_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    question_key: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    level: Mapped[str] = mapped_column(String(4), nullable=False)
    # 연결 base 문법 포인트 (D-8: base point only)
    grammar_point_id: Mapped[str] = mapped_column(String(60), nullable=False)
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    # 학습자 가독성 보강(정빈님 verify 발견): 후리가나(ruby HTML) + 한국어 번역.
    stem_furigana: Mapped[str | None] = mapped_column(Text, nullable=True)
    stem_ko: Mapped[str | None] = mapped_column(Text, nullable=True)
    # choices 항목은 {"key","text"} + 선택적 "text_ko"(한국어 번역, 데이터 확장).
    choices: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    correct_choice: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation_ko: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("level IN ('N1','N2','N3','N4','N5')", name="level"),
        Index("idx_diagq_level", "level"),
    )


class DiagnosticAnswer(CreatedAtMixin, Base):
    """진단 문항별 사용자 답안."""

    __tablename__ = "diagnostic_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    diagnostic_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("diagnostic_sessions.id"),
        nullable=False,
    )
    question_id: Mapped[str] = mapped_column(String(100), nullable=False)
    grammar_point_id: Mapped[str] = mapped_column(String(100), nullable=False)
    selected_choice: Mapped[str] = mapped_column(String(255), nullable=False)
    correct_choice: Mapped[str] = mapped_column(String(255), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    time_spent_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "diagnostic_session_id", "question_id", name="diag_answer_session_question"
        ),
        Index("idx_diag_answers_session", "diagnostic_session_id"),
    )
