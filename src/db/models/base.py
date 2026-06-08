"""SQLAlchemy 선언적 기반 클래스 + 공통 믹스인.

- `Base`: 결정적 제약 이름을 위한 naming_convention 포함 DeclarativeBase.
- `TimestampMixin`: created_at + updated_at (생성·수정 시각 모두 필요한 테이블).
- `CreatedAtMixin`: created_at만 필요한 테이블 (예: 답안, 캐시).

근거: naming_convention을 Base와 Alembic env.py에 동일 적용해야
autogenerate 제약 이름이 결정적이 되어 squash 충돌을 막는다 (세션 1 REC-13).
"""

from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """모든 ORM 모델의 선언적 기반."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    """created_at + updated_at 자동 컬럼."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class CreatedAtMixin:
    """created_at만 필요한 테이블용 믹스인."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
