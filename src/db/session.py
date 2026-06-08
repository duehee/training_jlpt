"""async DB 엔진 / 세션 팩토리.

FastAPI 의존성(`get_session`)과 health readiness 체크에서 사용한다.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """요청 단위 async 세션 의존성."""
    async with SessionLocal() as session:
        yield session
