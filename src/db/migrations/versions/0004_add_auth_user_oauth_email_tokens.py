"""add auth columns to users + oauth_accounts + email_verification_tokens

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-08

세션 9 인증 트랙 — 정빈님 결정 9건 반영.
- users: password_hash(bcrypt, NULL=OAuth 전용) + email_verified + email NOT NULL 승격(Q7)
- oauth_accounts 신설(Q5 = 별도 테이블, user_id FK CASCADE, provider 유니크)
- email_verification_tokens 신설(§b, Q6 TTL=24h — TTL은 애플리케이션 계층에서 부여)

email NOT NULL 승격 안전성: 적용 시점 users 0행(email NULL 0건) 사전 확인 → backfill 불필요.
anonymous_sessions.linked_user_id FK는 0001에 이미 존재 → 본 마이그레이션 미포함(익명 승격은 스키마 변경 없는 로직 작업).
FK/인덱스 명칭 63자 한도 사전 검증 완료(최장 fk_email_verification_tokens_user_id_users=42자).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── users 확장 ──
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    # Q7: email NOT NULL 승격 (users 0행 → 무해). unique(uq_users_email)는 0001 유지.
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    # ── oauth_accounts 신설 (Q5) ──
    op.create_table(
        "oauth_accounts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("provider_account_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_oauth_accounts_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_oauth_accounts"),
    )
    op.create_index(
        "uq_oauth_accounts_provider_account",
        "oauth_accounts",
        ["provider", "provider_account_id"],
        unique=True,
    )
    op.create_index("ix_oauth_accounts_user_id", "oauth_accounts", ["user_id"])

    # ── email_verification_tokens 신설 (§b) ──
    op.create_table(
        "email_verification_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_email_verification_tokens_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_email_verification_tokens"),
    )
    op.create_index(
        "ix_evt_token_hash",
        "email_verification_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_evt_user_id", "email_verification_tokens", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_evt_user_id", table_name="email_verification_tokens")
    op.drop_index("ix_evt_token_hash", table_name="email_verification_tokens")
    op.drop_table("email_verification_tokens")

    op.drop_index("ix_oauth_accounts_user_id", table_name="oauth_accounts")
    op.drop_index("uq_oauth_accounts_provider_account", table_name="oauth_accounts")
    op.drop_table("oauth_accounts")

    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=255),
        nullable=True,
    )
    op.drop_column("users", "email_verified")
    op.drop_column("users", "password_hash")
