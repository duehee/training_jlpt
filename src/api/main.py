"""FastAPI 엔트리포인트.

실행: poetry run uvicorn src.api.main:app --reload
"""

from fastapi import FastAPI

from src.api.routes import health
from src.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(health.router, prefix="/health", tags=["health"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"app": settings.app_name, "version": settings.app_version}
