"""회원 모델 (database_schema.md §5).

users — 로그인 사용자 기준 정보. 익명 진단 후 가입 추적(initial_diagnostic_session_id).
학습 기록 모델(learning_sessions 등)은 learning.py 참조.
인증 확장(세션 9): 비밀번호 해시 / 이메일 확인 / OAuth 계정 연결.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base, CreatedAtMixin, TimestampMixin


class User(TimestampMixin, Base):
    """로그인 사용자 기준 정보."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    # 세션 9 Q7(정빈님) — email NOT NULL 승격. 로그인 식별자로 관리.
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    # bcrypt 해시(60자). OAuth 전용 가입자는 NULL(비밀번호 없음). 세션 9 Q2.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 이메일 확인 완료 여부. 회원가입 직후 False, 확인 링크 클릭 시 True.
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
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
    # OAuth 계정 양방향 관리(세션 9 Q5). user 삭제 시 연결 계정 함께 삭제.
    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class OAuthAccount(CreatedAtMixin, Base):
    """소셜 로그인 계정 연결(세션 9 Q5 = 별도 테이블).

    provider(google 등) + provider_account_id(예: Google 'sub')로 외부 계정을 식별,
    한 user에 복수 provider 연결 확장 대비. 이메일/PW 계정과 동일 users 행에 연결.
    """

    __tablename__ = "oauth_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE", name="fk_oauth_accounts_user_id_users"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # provider가 반환한 이메일(참고용, 계정 매칭 근거).
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="oauth_accounts")

    __table_args__ = (
        # 동일 외부 계정의 중복 연결 방지(로그인 정합).
        Index(
            "uq_oauth_accounts_provider_account",
            "provider",
            "provider_account_id",
            unique=True,
        ),
        Index("ix_oauth_accounts_user_id", "user_id"),
    )


class EmailVerificationToken(CreatedAtMixin, Base):
    """이메일 확인 토큰(세션 9 §b, Q6 TTL=24h).

    raw 토큰은 확인 메일 URL에만 실리고 DB엔 sha256 해시만 저장(유출 대비).
    확인 시 consumed_at 기록으로 재사용 방지. 재발송은 구 토큰 소비 후 신규 발급.
    """

    __tablename__ = "email_verification_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            name="fk_email_verification_tokens_user_id_users",
        ),
        nullable=False,
    )
    # sha256(raw_token) hex(64자). raw는 저장하지 않는다.
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_evt_token_hash", "token_hash", unique=True),
        Index("ix_evt_user_id", "user_id"),
    )
