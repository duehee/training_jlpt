"""웹 쿠키 상수 (HTTP presentation 관심사).

세션 데이터 CRUD(생성·해소·활성 포인터)는 domains/session/service로 이관됨.
여기에는 쿠키 이름·수명 등 HTTP 계층 값만 남긴다.
"""

COOKIE_NAME = "session_id"
COOKIE_MAX_AGE = 24 * 60 * 60  # 24h (익명 세션 TTL과 일치)
