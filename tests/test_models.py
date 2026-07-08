"""ORM 모델 메타데이터 단위 테스트 (DB 연결 불필요).

재설계 target 스키마(04_target_db_design.md)의 핵심 불변식을 고정한다.
"""

from src.db.models import (
    Base,
    Chunk,
    ComparisonPair,
    EmailVerificationToken,
    OAuthAccount,
    User,
    WeakPoint,
)

EXPECTED_TABLES = {
    "chunks",
    "comparison_pairs",
    "diagnostic_questions",
    "anonymous_sessions",
    "diagnostic_sessions",
    "diagnostic_answers",
    "users",
    # 세션 9 인증 트랙 신설
    "oauth_accounts",
    "email_verification_tokens",
    "learning_sessions",
    "learning_records",
    "weak_points",
    "last_session",
    "llm_response_cache",
}


def test_fourteen_tables_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES
    assert len(Base.metadata.tables) == 14


def test_user_auth_columns_present() -> None:
    """세션 9 인증 확장 — 비밀번호 해시 / 이메일 확인 / email NOT NULL(Q7)."""
    cols = User.__table__.columns
    assert {"password_hash", "email_verified"} <= set(cols.keys())
    assert cols["email"].nullable is False
    assert cols["password_hash"].nullable is True


def test_oauth_account_unique_and_cascade() -> None:
    """OAuth 계정 — provider 유니크 + user 삭제 CASCADE(Q5)."""
    idx_names = {ix.name for ix in OAuthAccount.__table__.indexes}
    assert "uq_oauth_accounts_provider_account" in idx_names
    fk = next(iter(OAuthAccount.__table__.foreign_keys))
    assert fk.ondelete == "CASCADE"


def test_email_verification_token_hash_only() -> None:
    """확인 토큰 — raw 미저장(token_hash 컬럼) + 재사용 방지 consumed_at."""
    cols = set(EmailVerificationToken.__table__.columns.keys())
    assert {"token_hash", "expires_at", "consumed_at"} <= cols
    assert "token" not in cols


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
