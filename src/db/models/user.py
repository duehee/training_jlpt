"""회원 모델 (database_schema.md §5).

users — 로그인 사용자 기준 정보. 익명 진단 후 가입 추적(initial_diagnostic_session_id).
학습 기록 모델(learning_sessions 등)은 learning.py 참조.
"""

import uuid

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
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
