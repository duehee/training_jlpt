"""initial schema — 12 테이블 (재설계 target, 04_target_db_design.md)

Revision ID: 0001
Revises:
Create Date: 2026-06-06

콘텐츠 도메인: chunks / comparison_pairs
진단 도메인: anonymous_sessions / diagnostic_sessions / diagnostic_questions / diagnostic_answers
학습 도메인: users / learning_sessions / learning_records / weak_points / last_session
캐시: llm_response_cache

순환 FK(users ↔ diagnostic_sessions ↔ anonymous_sessions)는 테이블 생성 후
ALTER TABLE로 추가한다 (use_alter 패턴).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ── chunks ──
    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("chunk_key", sa.String(length=60), nullable=False),
        sa.Column("level", sa.String(length=4), nullable=False),
        sa.Column("chunk_type", sa.String(length=16), nullable=False),
        sa.Column("grammar_point_id", sa.String(length=60), nullable=True),
        sa.Column("base_point_id", sa.String(length=60), nullable=True),
        sa.Column("border_flag", sa.Boolean(), nullable=True),
        sa.Column("body", postgresql.JSONB(), nullable=False),
        sa.Column("l3_tags", postgresql.JSONB(), nullable=True),
        sa.Column("border_meta", postgresql.JSONB(), nullable=True),
        sa.Column("embedding_text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("source_status", sa.String(length=16), server_default="draft", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("chunk_type IN ('point','compare','variant')", name="chunk_type"),
        sa.CheckConstraint("level IN ('N1','N2','N3','N4','N5')", name="level"),
        sa.PrimaryKeyConstraint("id", name="pk_chunks"),
        sa.UniqueConstraint("chunk_key", name="uq_chunks_chunk_key"),
    )
    op.create_index("idx_chunks_level", "chunks", ["level"])
    op.create_index("idx_chunks_type", "chunks", ["chunk_type"])
    op.create_index("idx_chunks_level_type", "chunks", ["level", "chunk_type"])
    op.create_index("idx_chunks_grammar_point", "chunks", ["grammar_point_id"])
    op.create_index("idx_chunks_border", "chunks", ["border_flag"], postgresql_where=sa.text("border_flag = TRUE"))

    # ── comparison_pairs ──
    op.create_table(
        "comparison_pairs",
        sa.Column("compare_id", sa.String(length=60), nullable=False),
        sa.Column("level", sa.String(length=4), nullable=False),
        sa.Column("left_point_id", sa.String(length=60), nullable=False),
        sa.Column("right_point_id", sa.String(length=60), nullable=False),
        sa.Column("cluster", sa.String(length=4), nullable=False),
        sa.Column("star_weight", sa.SmallInteger(), nullable=False),
        sa.Column("confusion_point", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("star_weight BETWEEN 1 AND 3", name="star_weight"),
        sa.PrimaryKeyConstraint("compare_id", name="pk_comparison_pairs"),
    )
    op.create_index("idx_cmp_pairs_level", "comparison_pairs", ["level"])
    op.create_index("idx_cmp_pairs_points", "comparison_pairs", ["left_point_id", "right_point_id"])

    # ── diagnostic_questions ──
    op.create_table(
        "diagnostic_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("question_key", sa.String(length=60), nullable=False),
        sa.Column("level", sa.String(length=4), nullable=False),
        sa.Column("grammar_point_id", sa.String(length=60), nullable=False),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("choices", postgresql.JSONB(), nullable=False),
        sa.Column("correct_choice", sa.String(length=255), nullable=False),
        sa.Column("explanation_ko", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("level IN ('N1','N2','N3','N4','N5')", name="level"),
        sa.PrimaryKeyConstraint("id", name="pk_diagnostic_questions"),
        sa.UniqueConstraint("question_key", name="uq_diagnostic_questions_question_key"),
    )
    op.create_index("idx_diagq_level", "diagnostic_questions", ["level"])

    # ── llm_response_cache ──
    op.create_table(
        "llm_response_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cache_key", sa.String(length=255), nullable=False),
        sa.Column("prompt_hash", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column("token_usage", postgresql.JSONB(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_llm_response_cache"),
        sa.UniqueConstraint("cache_key", name="uq_llm_response_cache_cache_key"),
    )
    op.create_index("idx_llm_cache_key", "llm_response_cache", ["cache_key"])

    # ── anonymous_sessions (linked_user_id FK는 뒤에서 ALTER) ──
    op.create_table(
        "anonymous_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_token", sa.String(length=255), nullable=False),
        sa.Column("linked_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("diagnostic_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_anonymous_sessions"),
        sa.UniqueConstraint("session_token", name="uq_anonymous_sessions_session_token"),
    )
    op.create_index("idx_anon_sessions_linked_user", "anonymous_sessions", ["linked_user_id"])

    # ── users (initial_diagnostic_session_id FK는 뒤에서 ALTER) ──
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("nickname", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("current_level", sa.String(length=10), nullable=True),
        sa.Column("target_level", sa.String(length=10), nullable=True),
        sa.Column("initial_diagnostic_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # ── diagnostic_sessions (anonymous_session_id FK 인라인) ──
    op.create_table(
        "diagnostic_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("anonymous_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mode", sa.String(length=50), nullable=False),
        sa.Column("diagnosed_level", sa.String(length=10), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("max_score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["anonymous_session_id"], ["anonymous_sessions.id"], name="fk_diagnostic_sessions_anonymous_session_id_anonymous_sessions"),
        sa.PrimaryKeyConstraint("id", name="pk_diagnostic_sessions"),
    )
    op.create_index("idx_diag_sessions_anon", "diagnostic_sessions", ["anonymous_session_id"])

    # ── diagnostic_answers ──
    op.create_table(
        "diagnostic_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("diagnostic_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", sa.String(length=100), nullable=False),
        sa.Column("grammar_point_id", sa.String(length=100), nullable=False),
        sa.Column("selected_choice", sa.String(length=255), nullable=False),
        sa.Column("correct_choice", sa.String(length=255), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("time_spent_sec", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["diagnostic_session_id"], ["diagnostic_sessions.id"], name="fk_diagnostic_answers_diagnostic_session_id_diagnostic_sessions"),
        sa.PrimaryKeyConstraint("id", name="pk_diagnostic_answers"),
        sa.UniqueConstraint("diagnostic_session_id", "question_id", name="diag_answer_session_question"),
    )
    op.create_index("idx_diag_answers_session", "diagnostic_answers", ["diagnostic_session_id"])

    # ── learning_sessions ──
    op.create_table(
        "learning_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("grammar_point_id", sa.String(length=100), nullable=False),
        sa.Column("level", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("explanation_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_learning_sessions_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_learning_sessions"),
    )
    op.create_index("idx_learning_sessions_user", "learning_sessions", ["user_id"])

    # ── learning_records ──
    op.create_table(
        "learning_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("grammar_point_id", sa.String(length=100), nullable=False),
        sa.Column("level", sa.String(length=10), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("correct_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("mastery_score", sa.Numeric(precision=4, scale=3), server_default=sa.text("0.0"), nullable=False),
        sa.Column("last_result", sa.String(length=30), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_learning_records_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_learning_records"),
        sa.UniqueConstraint("user_id", "grammar_point_id", name="learning_record_user_gp"),
    )
    op.create_index("idx_learning_records_user_gp", "learning_records", ["user_id", "grammar_point_id"])
    op.create_index("idx_learning_records_next_review", "learning_records", ["next_review_at"], postgresql_where=sa.text("next_review_at IS NOT NULL"))

    # ── weak_points (컬럼명 metadata) ──
    op.create_table(
        "weak_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("grammar_point_id", sa.String(length=100), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("error_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("identified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_weak_points_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_weak_points"),
        sa.UniqueConstraint("user_id", "grammar_point_id", name="weak_point_user_gp"),
    )
    op.create_index("idx_weak_points_user_gp", "weak_points", ["user_id", "grammar_point_id"])
    op.create_index("idx_weak_points_user_error", "weak_points", ["user_id", sa.text("error_count DESC")])

    # ── last_session ──
    op.create_table(
        "last_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("learning_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("grammar_point_id", sa.String(length=100), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_last_session_user_id_users"),
        sa.ForeignKeyConstraint(["learning_session_id"], ["learning_sessions.id"], name="fk_last_session_learning_session_id_learning_sessions"),
        sa.PrimaryKeyConstraint("id", name="pk_last_session"),
        sa.UniqueConstraint("user_id", name="uq_last_session_user_id"),
    )
    op.create_index("idx_last_session_user", "last_session", ["user_id"])

    # ── 순환 FK (ALTER) ──
    op.create_foreign_key(
        "fk_anonymous_sessions_linked_user_id_users",
        "anonymous_sessions", "users", ["linked_user_id"], ["id"],
    )
    op.create_foreign_key(
        "fk_users_initial_diagnostic_session_id_diagnostic_sessions",
        "users", "diagnostic_sessions", ["initial_diagnostic_session_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_initial_diagnostic_session_id_diagnostic_sessions", "users", type_="foreignkey")
    op.drop_constraint("fk_anonymous_sessions_linked_user_id_users", "anonymous_sessions", type_="foreignkey")
    op.drop_table("last_session")
    op.drop_table("weak_points")
    op.drop_table("learning_records")
    op.drop_table("learning_sessions")
    op.drop_table("diagnostic_answers")
    op.drop_table("diagnostic_sessions")
    op.drop_table("users")
    op.drop_table("anonymous_sessions")
    op.drop_table("llm_response_cache")
    op.drop_table("diagnostic_questions")
    op.drop_table("comparison_pairs")
    op.drop_table("chunks")
