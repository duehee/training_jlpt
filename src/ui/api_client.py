"""진단 API 얇은 클라이언트 (consumer 계약 06).

stdlib `urllib.request`만 사용 — 런타임 의존성 추가 없음 (lead 확정 2026-06-17).
모든 호출은 06 정식 계약의 엔드포인트/응답에 1:1 대응한다.
에러는 `ApiError`(status_code + code + message)로 정규화해 UI가 한국어 메시지로 매핑한다.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

# API base URL — 기본 로컬 uvicorn. 환경변수로 덮어쓰기 가능.
DEFAULT_BASE_URL = os.environ.get("JLPT_API_BASE_URL", "http://localhost:8000")

_TIMEOUT_SEC = 30  # explanation은 LLM 호출이라 캐시 미스 시 수 초 소요 가능.


class ApiError(Exception):
    """API 호출 실패 정규화. status_code=0 은 네트워크/연결 실패."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"[{status_code}/{code}] {message}")


def parse_error_payload(status_code: int, raw_body: str) -> ApiError:
    """에러 응답 바디를 `ApiError`로 변환 (순수 — 단위 테스트 대상).

    FastAPI 기본 에러는 `{"detail": "..."}`, 계약 §3-2 포맷은 `{"error": {...}}`.
    둘 다 흡수한다.
    """
    code = "HTTP_ERROR"
    message = raw_body.strip() or "요청 처리 중 오류가 발생했습니다."
    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, ValueError):
        return ApiError(status_code, code, message)

    if isinstance(payload, dict):
        err = payload.get("error")
        if isinstance(err, dict):  # 계약 §3-2 포맷
            code = str(err.get("code", code))
            message = str(err.get("message", message))
        elif "detail" in payload:  # FastAPI 기본
            message = str(payload["detail"])
    return ApiError(status_code, code, message)


class ApiClient:
    """진단 한 사이클 API 래퍼. 익명 세션 토큰을 보관한다."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self.session_token: str | None = None

    # ── 내부 ──
    def _request(
        self, method: str, path: str, body: dict[str, Any] | None = None, *, auth: bool = True
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"}
        if auth:
            if not self.session_token:
                raise ApiError(0, "NO_SESSION", "세션 토큰이 없습니다. 진단을 다시 시작해 주세요.")
            headers["Authorization"] = f"Session {self.session_token}"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT_SEC) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            raise parse_error_payload(exc.code, raw_body) from exc
        except urllib.error.URLError as exc:
            raise ApiError(0, "CONNECTION_ERROR", f"API 서버에 연결할 수 없습니다 ({exc.reason}).") from exc

        if not raw:
            return {}
        return json.loads(raw)

    # ── 06 §1 익명 세션 ──
    def create_anonymous_session(self) -> dict[str, Any]:
        data = self._request("POST", "/api/v1/sessions/anonymous", auth=False)
        self.session_token = data.get("session_token")
        return data

    # ── 06 §2 진단 시작 ──
    def start_diagnosis(self) -> dict[str, Any]:
        return self._request(
            "POST", "/api/v1/diagnosis/sessions", {"mode": "initial_assessment"}
        )

    # ── 06 §3 출제 ──
    def get_questions(self, diagnosis_session_id: str) -> dict[str, Any]:
        return self._request(
            "GET", f"/api/v1/diagnosis/sessions/{diagnosis_session_id}/questions"
        )

    # ── 06 §4 답안 제출 ──
    def submit_answer(
        self, diagnosis_session_id: str, question_id: str, selected_choice: str, time_spent_sec: int | None = None
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/diagnosis/sessions/{diagnosis_session_id}/answers",
            {"question_id": question_id, "selected_choice": selected_choice, "time_spent_sec": time_spent_sec},
        )

    # ── 06 §5 완료 ──
    def complete(self, diagnosis_session_id: str) -> dict[str, Any]:
        return self._request(
            "POST", f"/api/v1/diagnosis/sessions/{diagnosis_session_id}/complete"
        )

    # ── 06 §7 explanation 프리뷰 (게스트) ──
    def get_explanation(self, diagnosis_session_id: str, grammar_point_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/api/v1/diagnosis/sessions/{diagnosis_session_id}/explanation/{grammar_point_id}",
        )
