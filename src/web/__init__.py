"""웹 SSR 레이어 (design_backend Jinja2 시안 이식, Phase 1 4 화면).

라우트는 기존 진단 라우트 핸들러를 같은 ASGI app 안에서 in-process 직접 호출해
실 데이터를 채운다(httpx 우회). 세션 상태는 쿠키 `session_id` →
`anonymous_sessions.active_diagnostic_session_id`(마이그레이션 0003) 1홉으로 해소한다.

기존 `src/ui/`(Streamlit)와 병행 운영한다.
"""
