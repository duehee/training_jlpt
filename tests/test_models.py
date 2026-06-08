"""ORM 모델 메타데이터 단위 테스트 (DB 연결 불필요).

재설계 target 스키마(04_target_db_design.md)의 핵심 불변식을 고정한다.
"""

from src.db.models import Base, Chunk, ComparisonPair, WeakPoint

EXPECTED_TABLES = {
    "chunks",
    "comparison_pairs",
    "diagnostic_questions",
    "anonymous_sessions",
    "diagnostic_sessions",
    "diagnostic_answers",
    "users",
    "learning_sessions",
    "learning_records",
    "weak_points",
    "last_session",
    "llm_response_cache",
}


def test_twelve_tables_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES
    assert len(Base.metadata.tables) == 12


def test_chunks_core_columns() -> None:
    cols = set(Chunk.__table__.columns.keys())
    required = {
        "chunk_key",
        "level",
        "chunk_type",
        "grammar_point_id",
        "base_point_id",
        "border_flag",
        "body",
        "l3_tags",
        "border_meta",
        "embedding_text",
        "embedding",
        "source_status",
    }
    assert required <= cols


def test_self_comparison_allowed() -> None:
    """자기 대조(106_ta 등)를 위해 left != right CHECK가 없어야 한다."""
    check_texts = " ".join(
        str(c.sqltext)
        for c in ComparisonPair.__table__.constraints
        if c.__class__.__name__ == "CheckConstraint"
    )
    assert "left_point_id" not in check_texts
    assert "right_point_id" not in check_texts


def test_weak_points_metadata_column_name() -> None:
    """SQLAlchemy 예약어 회피: 속성 meta → 컬럼명 metadata."""
    assert "metadata" in WeakPoint.__table__.columns.keys()
    assert "meta" not in WeakPoint.__table__.columns.keys()


def test_chunk_type_check_constraint_present() -> None:
    check_texts = " ".join(
        str(c.sqltext)
        for c in Chunk.__table__.constraints
        if c.__class__.__name__ == "CheckConstraint"
    )
    assert "chunk_type" in check_texts
    assert "level" in check_texts
