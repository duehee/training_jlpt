"""add diagnostic_questions.stem_furigana / stem_ko (학습자 가독성 보강)

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-17

정빈님 verify 발견 — 학습자가 진단 문항(일본어 stem)을 읽지 못함.
후리가나(ruby HTML)와 한국어 번역 컬럼을 추가한다 (둘 다 NULL 허용 — 기존 행 무해).
choices 내부 `text_ko`는 JSONB 데이터 확장이라 스키마 변경 없음.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "diagnostic_questions",
        sa.Column("stem_furigana", sa.Text(), nullable=True),
    )
    op.add_column(
        "diagnostic_questions",
        sa.Column("stem_ko", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("diagnostic_questions", "stem_ko")
    op.drop_column("diagnostic_questions", "stem_furigana")
