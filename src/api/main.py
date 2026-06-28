"""FastAPI 엔트리포인트.

실행: poetry run uvicorn src.api.main:app --reload
"""

from fastapi import FastAPI

from src.api.routes import diagnostic, health, sessions
from src.core.config import settings
from src.web.routes import router as web_router

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(
    diagnostic.router, prefix="/api/v1/diagnosis", tags=["diagnosis"]
)
# 웹 SSR(design_backend 이식). 루트 레벨 라우트(/, /quiz 등) → prefix 없음.
app.include_router(web_router)


@app.get("/api")
async def api_info() -> dict[str, str]:
    """앱 메타(구 `/` JSON). `/`는 SSR intro 전용으로 비움(세션 7 §7 (A))."""
    return {"app": settings.app_name, "version": settings.app_version}
