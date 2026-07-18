"""웹 쿠키 상수 (HTTP presentation 관심사).

세션 데이터 CRUD(생성·해소·활성 포인터)는 domains/session/service로 이관됨.
여기에는 쿠키 이름·수명 등 HTTP 계층 값만 남긴다.
"""

COOKIE_NAME = "session_id"
COOKIE_MAX_AGE = 24 * 60 * 60  # 24h (익명 세션 TTL과 일치)

# 로그인 JWT access token 쿠키 (세션 9 — OAuth callback + SSR 로그인 공용).
# 하린 web 로그인 폼도 이 이름을 재사용(통일). max_age는 JWT exp와 일치.
ACCESS_COOKIE_NAME = "access_token"
# OAuth CSRF 방지용 state 쿠키 (authorize→callback 왕복 대조, 단명).
OAUTH_STATE_COOKIE_NAME = "oauth_state"
OAUTH_STATE_MAX_AGE = 10 * 60  # 10분 (동의 화면 왕복 여유)
