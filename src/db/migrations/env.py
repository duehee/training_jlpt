"""Alembic 마이그레이션 환경 (async, SQLAlchemy 2.0).

- 오프라인 모드: DB 연결 없이 SQL 스크립트 생성 (`alembic upgrade head --sql`).
- 온라인 모드: 실제 DB 연결로 마이그레이션 실행 (asyncpg).

`src.db.models`를 import해 모든 모델을 Base.metadata에 등록한다 (autogenerate 감지용).
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import src.db.models  # noqa: F401 — 모든 모델 import 트리거 (metadata 등록)
from src.core.config import settings
from src.db.models.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# alembic.ini의 빈 sqlalchemy.url을 settings에서 주입
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """오프라인 모드: DB 연결 없이 SQL 스크립트 생성."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """온라인 모드: 실제 DB 연결로 마이그레이션 실행 (async)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
