"""애플리케이션 서비스 레이어.

학습 루프의 LLM 호출·캐시·프롬프트·retrieval을 담는 패키지.
- `llm`    : provider 추상화 (Protocol) + OpenAI 구현 + 테스트용 Fake
- `cache`  : LLM 응답 캐시 (DB / in-memory), 캐시 키 전략
- `prompts`: 버전드 프롬프트 템플릿
- `learning`: retrieval + 설명/문제 생성 노드

설계 근거: `docs/planning/session_5/be_jaehyeon/01_learning_loop_plan.md`.
정책: 기본 모델 gpt-4o-mini, 모든 LLM 호출은 캐시 경유, `openai` 직접 호출은
`llm.openai_provider`로만 캡슐화 (provider 추상화 뒤로).
"""
