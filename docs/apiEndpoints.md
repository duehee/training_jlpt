# API 엔드포인트

> 최종 업데이트: 2026-04-14
> JLPT 개인 학습 에이전트의 Phase 1 API 경계를 정리한 문서입니다.

---

## 1. 설계 원칙

- 외부 인터페이스는 REST 기준으로 설계합니다.
- 비로그인 사용자와 로그인 사용자를 모두 고려합니다.
- 진단, 추천, 학습 리소스는 분리합니다.
- LangGraph는 내부 워크플로우로 두고, 외부에는 안정적인 HTTP API만 노출합니다.

---

## 2. Phase 1에서 다루는 흐름

Phase 1 API는 아래 흐름을 우선 지원합니다.

1. 익명 세션 생성
2. 진단 세션 시작
3. 진단 문제 조회
4. 진단 답안 제출
5. 진단 완료 및 결과 조회
6. 학습 포인트 추천
7. 학습 세션 시작
8. 문법 설명 조회
9. 확인 문제 답안 제출
10. 마지막 학습 지점 복귀

---

## 3. 엔드포인트 목록

### Health

#### `GET /health`

```json
{
  "status": "ok"
}
```

---

### Sessions

#### `POST /api/v1/sessions/anonymous`

진단 시작 전 익명 세션을 생성합니다.

```json
{
  "session_id": "anon_123",
  "expires_at": "2026-04-14T23:59:59Z"
}
```

#### `POST /api/v1/auth/link-session`

익명 세션 데이터를 로그인 사용자 계정과 연결합니다.

---

### Diagnosis

#### `POST /api/v1/diagnosis/sessions`

진단 세션을 시작합니다.

#### `GET /api/v1/diagnosis/sessions/{diagnosisSessionId}/questions`

진단 문제를 반환합니다.

#### `POST /api/v1/diagnosis/sessions/{diagnosisSessionId}/answers`

사용자 답안을 저장하고 채점합니다.

#### `POST /api/v1/diagnosis/sessions/{diagnosisSessionId}/complete`

진단 레벨, 약점 문법, 추천 시작 포인트를 계산합니다.

```json
{
  "diagnosed_level": "N4",
  "score": 6,
  "max_score": 10,
  "weak_points": ["〜ている", "〜ませんか"],
  "recommended_start_point": "〜ている"
}
```

#### `GET /api/v1/diagnosis/sessions/{diagnosisSessionId}/result`

이미 계산된 진단 결과를 다시 조회합니다.

---

### Recommendation

#### `GET /api/v1/recommendations/learning-path`

진단 결과와 학습 이력을 바탕으로 다음 문법 포인트를 추천합니다.

---

### Learning

#### `POST /api/v1/learning/sessions`

특정 문법 포인트에 대한 학습 세션을 시작합니다.

#### `GET /api/v1/learning/sessions/{learningSessionId}`

현재 학습 세션 상태를 반환합니다.

#### `GET /api/v1/learning/sessions/{learningSessionId}/explanation`

현재 문법 포인트에 대한 RAG 기반 설명과 예문을 반환합니다.

#### `POST /api/v1/learning/sessions/{learningSessionId}/answers`

확인 문제 답안을 제출하고 다음 분기를 결정합니다.

---

### Resume

#### `GET /api/v1/learning/resume`

현재 사용자의 마지막 학습 지점을 조회합니다.

---

## 4. 구현 메모

- 익명 세션은 나중에 로그인 계정과 연결 가능해야 합니다.
- MVP에서는 진단 문제를 한 번에 내려줘도 됩니다.
- 추천 로직은 가능하면 결정적 규칙을 우선하고, LLM 개입은 최소화합니다.
- Retrieval 백엔드는 PostgreSQL 16 + `pgvector`를 기준으로 합니다.
