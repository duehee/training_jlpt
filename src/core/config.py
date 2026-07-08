"""애플리케이션 설정 로더.

환경변수 / `.env`에서 설정을 읽는다. 평문 비밀번호를 코드에 두지 않는다.
기본값은 `docker-compose.yml`의 PostgreSQL 서비스와 정합 (jlpt_user/jlpt_password/jlpt_db).
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """프로젝트 전역 설정."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PostgreSQL 접속 (docker-compose.yml 환경변수와 동일 이름)
    postgres_user: str = "jlpt_user"
    postgres_password: str = "jlpt_password"
    postgres_db: str = "jlpt_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # .env에 완성된 URL이 있으면 우선 사용 (없으면 위 요소로 조합)
    database_url_override: str | None = Field(default=None, validation_alias="DATABASE_URL")

    # ── OpenAI (정빈님이 .env에 OPENAI_API_KEY=... 채우면 자동 로드) ──
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_chat_model: str = "gpt-4o-mini"          # 기본 (비용 절감)
    openai_chat_model_quality: str = "gpt-4o"       # 품질 중요 경로만
    embedding_model: str = "text-embedding-3-small"

    # ── JWT (세션 9 Q1=B) ──
    # 프로덕션은 반드시 .env의 JWT_SECRET_KEY로 override (dev 기본값은 서명 위조 방지 불가).
    jwt_secret_key: str = Field(
        default="dev-insecure-change-me", validation_alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24h (데모 기본)

    app_name: str = "jlpt-agent"
    app_version: str = "0.1.0"

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def database_url(self) -> str:
        """async(asyncpg) 드라이버용 DB URL."""
        if self.database_url_override:
            return self.database_url_override
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
