"""add anonymous_sessions.active_diagnostic_session_id FK

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-27

세션 7 (B) 결정 — 쿠키 `session_id` 단일 + DB 익명 세션 레코드에 활성 진단
세션 포인터를 둔다. 웹 SSR 레이어가 쿠키→anon→active_diagnostic_session_id를
1홉으로 해소한다.

순수 가산: nullable FK 컬럼 1개. 기존 anonymous_sessions 행은 NULL(= 활성 진단
없음)로 무해 → backfill 없음. 정방향 포인터라 diagnostic_sessions와 순환 FK가
되며(역방향 anonymous_session_id 기존 존재), ondelete=SET NULL로 diag 삭제 시
포인터 자동 NULL → cleanup/restart/재진단 정합.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Postgres 식별자 63자 한도 회피 위해 축약 (idx 명칭과 일관).
_FK_NAME = "fk_anon_sessions_active_diag_session_id"
_INDEX_NAME = "idx_anon_sessions_active_diag"


def upgrade() -> None:
    op.add_column(
        "anonymous_sessions",
        sa.Column(
            "active_diagnostic_session_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_index(
        _INDEX_NAME,
        "anonymous_sessions",
        ["active_diagnostic_session_id"],
    )
    op.create_foreign_key(
        _FK_NAME,
        "anonymous_sessions",
        "diagnostic_sessions",
        ["active_diagnostic_session_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(_FK_NAME, "anonymous_sessions", type_="foreignkey")
    op.drop_index(_INDEX_NAME, table_name="anonymous_sessions")
    op.drop_column("anonymous_sessions", "active_diagnostic_session_id")
