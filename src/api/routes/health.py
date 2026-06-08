"""헬스 체크 엔드포인트.

- `GET /health`        : liveness — 앱이 떠 있는지 (DB 무관)
- `GET /health/ready`  : readiness — DB 연결까지 정상인지
"""

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from src.core.config import settings
from src.db.session import engine

router = APIRouter(tags=["health"])


@router.get("")
async def health() -> dict[str, str]:
    """앱 생존 확인."""
    return {"status": "ok", "version": settings.app_version}


@router.get("/ready")
async def ready(response: Response) -> dict[str, str | bool]:
    """DB 연결 포함 준비 상태 확인."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        database_ok = True
    except Exception:
        database_ok = False

    if not database_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if database_ok else "degraded",
        "database": "ok" if database_ok else "error",
        "openai_key_configured": settings.has_openai_key,
    }
