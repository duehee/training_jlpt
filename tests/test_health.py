"""health 엔드포인트 테스트 (FastAPI TestClient).

readiness는 DB 연결을 확인하므로 docker PG가 떠 있어야 통과한다.
"""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_liveness() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_health_readiness_db_ok() -> None:
    res = client.get("/health/ready")
    assert res.status_code == 200
    body = res.json()
    assert body["database"] == "ok"
    assert body["status"] == "ok"
