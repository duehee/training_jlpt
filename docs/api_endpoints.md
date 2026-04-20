# API 엔드포인트

> 최종 업데이트: 2026-04-19
> 담당 축: **How-external** — 외부에 어떤 경계를 노출하는가
> 관련 문서: `service_flows.md`, `database_schema.md`, `implementation_roadmap.md`

---

## 📌 빠른 참조 (에이전트용)

**이 문서에서 찾을 수 있는 것**
- API 설계 원칙 → 1장
- URL 네이밍 규칙 → 2장
- 공통 규약 (인증/에러/페이징) → 3장
- Health → 4장
- 세션 API (익명/연결) → 5장
- 진단 API → 6장
- 추천 API → 7장
- 학습 API → 8장
- 이어하기 API → 9장
- 구현 체크리스트 → 10장

**이 문서에서 찾을 수 없는 것**
- 사용자 플로우 → `service_flows.md`
- DB 테이블 구조 → `database_schema.md`
- 구현 순서/일정 → `implementation_roadmap.md`
- 설계 결정 배경 → `decision_log.md`

---

## 이 문서는
JLPT 개인 학습 에이전트의 **Phase 1 HTTP API 계약**을 정의합니다.
모든 엔드포인트의 경로, 요청/응답 형식, 상태 코드, 관련 테이블을 이 문서에서 찾을 수 있습니다.

**에이전트가 API 구현 시 가장 먼저 참조할 문서**입니다.

---

## 1. 설계 원칙

- **REST 기반** 리소스 중심 설계
- 익명/로그인 사용자를 모두 고려
- 진단/추천/학습 리소스는 **분리** (한 리소스에 섞지 않음)
- **LangGraph는 내부 구현**이며 외부 API는 안정적 HTTP 계약만 노출
- Phase 1은 **동기 응답**이 기본 (LLM 스트리밍은 Phase 2 이후 고려)
- 응답은 **JSON 객체**로 통일 (배열 top-level 반환 금지)

---

## 2. URL 네이밍 규칙

### 2-1. 기본 구조

```
/api/v1/{resource}/{id}/{sub-resource}
```

### 2-2. 규칙

| 규칙 | 내용 |
|------|------|
| 버전 | 모든 API는 `/api/v1/` 프리픽스 |
| 리소스 | 복수형 사용 (`sessions`, `answers`) |
| ID 표기 | URL에서는 `camelCase` (`diagnosisSessionId`) |
| JSON 키 표기 | 응답/요청 바디는 `snake_case` |
| 동사 회피 | 리소스명은 명사. 액션은 하위 경로 (`/complete`) |

### 2-3. 예시

```
✅ GET    /api/v1/diagnosis/sessions/{diagnosisSessionId}/questions
✅ POST   /api/v1/learning/sessions/{learningSessionId}/answers
❌ GET    /api/v1/getDiagnosisQuestions
❌ POST   /api/v1/submitAnswer
```

---

## 3. 공통 규약

### 3-1. 인증

| 유형 | 표기 | 용도 |
|------|------|------|
| 익명 | `Authorization: Session {session_token}` | 진단까지의 흐름 |
| 회원 | `Authorization: Bearer {jwt_token}` | 학습, 이어하기 |
| 공개 | 없음 | `/health` |

각 엔드포인트 명세에 필요한 인증 유형을 **명시**합니다.

### 3-2. 에러 응답 포맷

모든 에러는 아래 구조로 반환합니다.

```json
{
  "error": {
    "code": "DIAGNOSTIC_SESSION_NOT_FOUND",
    "message": "진단 세션을 찾을 수 없습니다.",
    "details": {
      "session_id": "abc-123"
    }
  }
}
```

### 3-3. 주요 HTTP 상태 코드

| 코드 | 사용 사례 |
|------|-----------|
| `200 OK` | 성공 (조회, 수정) |
| `201 Created` | 리소스 생성 성공 |
| `204 No Content` | 성공했으나 응답 바디 없음 |
| `400 Bad Request` | 요청 형식 오류 |
| `401 Unauthorized` | 인증 실패 |
| `403 Forbidden` | 권한 없음 |
| `404 Not Found` | 리소스 없음 |
| `409 Conflict` | 상태 충돌 (예: 이미 완료된 진단 재완료 시도) |
| `422 Unprocessable Entity` | 검증 실패 (Pydantic 기본값) |
| `500 Internal Server Error` | 서버 오류 |

### 3-4. 페이징 (향후 대비)

Phase 1은 페이징이 필요한 리소스가 적어 기본값만 정의합니다.

```
?limit=20&cursor={opaque_cursor}
```

응답:

```json
{
  "items": [...],
  "next_cursor": "eyJ..."
}
```

---

## 4. Health

### `GET /health`

서비스 헬스 체크. 인증 불필요.

**응답 (200)**:

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

**관련 테이블**: 없음 (애플리케이션 수준)

---

## 5. 세션 API

### 5-1. `POST /api/v1/sessions/anonymous`

진단 시작 전 익명 세션을 생성합니다.

**인증**: 불필요

**요청 바디**: 없음

**응답 (201)**:

```json
{
  "session_token": "sess_abc123xyz...",
  "expires_at": "2026-04-20T10:00:00Z"
}
```

**관련 테이블**:
- `anonymous_sessions` (생성)

**에러**:
- `500 Internal Server Error`: 토큰 생성 실패

---

### 5-2. `POST /api/v1/auth/link-session`

익명 세션의 진단 결과를 로그인 사용자 계정과 연결합니다.
`database_schema.md` 4-4장의 **핵심 트랜잭션**을 실행하는 API입니다.

**인증**: 익명 세션 (`Authorization: Session {session_token}`)

**요청 바디**:

```json
{
  "login_type": "nickname",
  "nickname": "듀히",
  "email": null
}
```

**응답 (200)**:

```json
{
  "user_id": "user-uuid",
  "nickname": "정빈",
  "current_level": "N4",
  "initial_diagnostic_session_id": "diag-uuid",
  "weak_points": [
    {
      "grammar_point_id": "grammar_n5_011",
      "error_count": 2
    },
    {
      "grammar_point_id": "grammar_n4_023",
      "error_count": 1
    }
  ],
  "recommended_start_point": "grammar_n5_011"
}
```

**관련 테이블** (단일 트랜잭션):
- `users` (생성/조회)
- `anonymous_sessions.linked_user_id` (갱신)
- `users.initial_diagnostic_session_id` (갱신)
- `users.current_level` (갱신)
- `weak_points` (일괄 생성)

**에러**:
- `400 Bad Request`: `login_type` 미지원
- `401 Unauthorized`: 익명 세션 무효
- `404 Not Found`: 진단 세션이 완료되지 않음
- `409 Conflict`: 이미 연결된 세션

---

## 6. 진단 API

### 6-1. `POST /api/v1/diagnosis/sessions`

진단 세션을 시작합니다.

**인증**: 익명 세션

**요청 바디**:

```json
{
  "mode": "initial_assessment"
}
```

**응답 (201)**:

```json
{
  "diagnostic_session_id": "diag-uuid",
  "status": "started",
  "max_score": 10,
  "started_at": "2026-04-19T10:00:00Z"
}
```

**관련 테이블**:
- `diagnostic_sessions` (생성, `anonymous_session_id` 연결)

---

### 6-2. `GET /api/v1/diagnosis/sessions/{diagnosisSessionId}/questions`

진단 문제를 반환합니다. Phase 1은 10문항을 한 번에 반환합니다.

**인증**: 익명 세션

**응답 (200)**:

```json
{
  "diagnostic_session_id": "diag-uuid",
  "questions": [
    {
      "question_id": "q_n5_001",
      "grammar_point_id": "grammar_n5_001",
      "level": "N5",
      "prompt": "私___学生です。",
      "choices": [
        { "key": "A", "text": "は" },
        { "key": "B", "text": "が" },
        { "key": "C", "text": "を" },
        { "key": "D", "text": "に" }
      ]
    }
  ]
}
```

**관련 테이블**:
- `diagnostic_sessions` (조회, status 확인)
- 진단 문제 seed 데이터 (저장소 확정 필요 — 미결 사항)

**메모**:
- 문제는 **정답을 포함하지 않음** (보안상 서버에서만 채점)
- Phase 2에서는 LLM 보조 문제 생성 고려

---

### 6-3. `POST /api/v1/diagnosis/sessions/{diagnosisSessionId}/answers`

답안을 제출합니다. 문항별 제출 방식.

**인증**: 익명 세션

**요청 바디**:

```json
{
  "question_id": "q_n5_001",
  "selected_choice": "A",
  "time_spent_sec": 12
}
```

**응답 (201)**:

```json
{
  "answer_id": "ans-uuid",
  "is_correct": true,
  "progress": {
    "answered": 3,
    "total": 10
  }
}
```

**관련 테이블**:
- `diagnostic_answers` (생성)
- `diagnostic_sessions.status` (`started` → `in_progress`)

**에러**:
- `409 Conflict`: 이미 해당 question_id 답안 존재 (`UNIQUE` 제약 위반)
- `409 Conflict`: 이미 완료된 진단 세션

---

### 6-4. `POST /api/v1/diagnosis/sessions/{diagnosisSessionId}/complete`

진단을 완료 처리하고 결과를 계산합니다.

**인증**: 익명 세션

**요청 바디**: 없음

**응답 (200)**:

```json
{
  "diagnostic_session_id": "diag-uuid",
  "diagnosed_level": "N4",
  "score": 6,
  "max_score": 10,
  "weak_grammar_points": [
    {
      "grammar_point_id": "grammar_n5_011",
      "error_count": 2,
      "level": "N5"
    }
  ],
  "recommended_start_point": "grammar_n5_011",
  "completed_at": "2026-04-19T10:15:00Z"
}
```

**관련 테이블**:
- `diagnostic_sessions` (갱신: `diagnosed_level`, `score`, `status='completed'`, `completed_at`)
- `diagnostic_answers` (집계 조회)
- `anonymous_sessions.diagnostic_completed_at` (갱신)

**메모**:
- **이 시점에는 `weak_points` 테이블에 쓰지 않습니다.** 로그인 시점에 한 번만 생성.
- `diagnosed_level` 계산 규칙: 미결 사항 (담당: 재현 + 민석)

**에러**:
- `409 Conflict`: 이미 완료됨
- `400 Bad Request`: 미완료 답안 존재 (답안 수 < 10)

---

### 6-5. `GET /api/v1/diagnosis/sessions/{diagnosisSessionId}/result`

이미 계산된 진단 결과를 조회합니다.

**인증**: 익명 세션 또는 회원 (진단 소유자)

**응답 (200)**: 6-4와 동일 구조

**메모**:
- 로그인 후 결과 재확인 UI용.
- `users.initial_diagnostic_session_id`로 역참조 가능하면 회원도 접근 허용.

---

## 7. 추천 API

### 7-1. `GET /api/v1/recommendations/learning-path`

진단 결과와 학습 이력을 바탕으로 다음 학습 포인트를 추천합니다.

**인증**: 회원

**쿼리 파라미터**:
- `limit` (optional, default=5): 반환 포인트 수

**응답 (200)**:

```json
{
  "recommendations": [
    {
      "grammar_point_id": "grammar_n5_011",
      "level": "N5",
      "priority": 1,
      "reason": "diagnosis_weak",
      "error_count": 2
    },
    {
      "grammar_point_id": "grammar_n5_023",
      "level": "N5",
      "priority": 2,
      "reason": "learning_weak",
      "error_count": 1
    }
  ]
}
```

**관련 테이블**:
- `weak_points` (우선순위 원천)
- `learning_records` (이력 참고)

**메모**:
- Phase 1은 **규칙 기반 추천** (error_count DESC).
- LLM 개입은 최소화 (비용 + 일관성).
- `reason`: `diagnosis_weak`, `learning_weak`, `next_level`, `review` 중 하나.

---

## 8. 학습 API

### 8-1. `POST /api/v1/learning/sessions`

특정 문법 포인트에 대한 학습 세션을 시작합니다.

**인증**: 회원

**요청 바디**:

```json
{
  "grammar_point_id": "grammar_n5_011",
  "level": "N5"
}
```

**응답 (201)**:

```json
{
  "learning_session_id": "learn-uuid",
  "grammar_point_id": "grammar_n5_011",
  "level": "N5",
  "status": "started",
  "explanation_version": 1,
  "started_at": "2026-04-19T10:30:00Z"
}
```

**관련 테이블**:
- `learning_sessions` (생성)
- `last_session` (UPSERT: `user_id` 기준)

---

### 8-2. `GET /api/v1/learning/sessions/{learningSessionId}`

현재 학습 세션 상태를 반환합니다.

**인증**: 회원 (세션 소유자)

**응답 (200)**:

```json
{
  "learning_session_id": "learn-uuid",
  "grammar_point_id": "grammar_n5_011",
  "level": "N5",
  "status": "in_progress",
  "explanation_version": 1,
  "started_at": "2026-04-19T10:30:00Z"
}
```

**관련 테이블**:
- `learning_sessions` (조회)

---

### 8-3. `GET /api/v1/learning/sessions/{learningSessionId}/explanation`

현재 문법 포인트에 대한 RAG 기반 설명과 예문을 반환합니다.

**인증**: 회원 (세션 소유자)

**응답 (200)**:

```json
{
  "learning_session_id": "learn-uuid",
  "grammar_point_id": "grammar_n5_011",
  "explanation_version": 1,
  "grammar_chunk": {
    "chunk_serial": "N5_grammar_011",
    "point": "が",
    "meaning_ko": "주격조사. 주어를 강조하거나 새로운 정보를 제시할 때 사용...",
    "connection": "명사 + が",
    "examples": [
      { "jp": "雨が降っています。", "ko": "비가 내리고 있습니다." }
    ]
  },
  "compare_chunks": [
    {
      "chunk_serial": "N5_compare_001",
      "pair": ["は", "が"],
      "confusion_point": "주제 표시 vs 주어 강조",
      "explanation_ko": "..."
    }
  ],
  "generated_explanation": "が는 주어를 드러낼 때 사용하며, 특히 새로운 정보를 소개할 때 적합합니다...",
  "cached": true
}
```

**관련 테이블**:
- `grammar_chunks` (retrieval)
- `llm_response_cache` (캐시 히트 확인 및 저장)

**메모**:
- `cached: true`면 캐시에서 가져옴 (비용 0).
- `cached: false`면 LLM 호출 + 캐시 저장.
- `explanation_version`이 2 이상이면 재설명 프롬프트로 변형 후 호출.

---

### 8-4. `POST /api/v1/learning/sessions/{learningSessionId}/question`

이해도 확인 문제를 생성/조회합니다.

**인증**: 회원 (세션 소유자)

**응답 (200)**:

```json
{
  "question": {
    "prompt": "雨___降っています。",
    "choices": [
      { "key": "A", "text": "は" },
      { "key": "B", "text": "が" },
      { "key": "C", "text": "を" },
      { "key": "D", "text": "に" }
    ]
  },
  "cached": true
}
```

**관련 테이블**:
- `llm_response_cache` (캐시 활용)

**메모**:
- 정답은 서버에서만 보유. 응답에 포함하지 않음.
- 같은 `learning_session_id` + `explanation_version`은 같은 문제를 반환.

---

### 8-5. `POST /api/v1/learning/sessions/{learningSessionId}/answers`

이해도 확인 문제의 답안을 제출합니다.

**인증**: 회원 (세션 소유자)

**요청 바디**:

```json
{
  "selected_choice": "B"
}
```

**응답 (200)**:

```json
{
  "is_correct": true,
  "next_action": "advance",
  "explanation_version": 1,
  "learning_session_status": "completed",
  "mastery_score": 0.650,
  "next_recommendation": {
    "grammar_point_id": "grammar_n5_023",
    "level": "N5"
  }
}
```

**`next_action` 값**:

| 값 | 의미 | 조건 |
|----|------|------|
| `advance` | 다음 학습 포인트로 이동 | 정답 |
| `retry` | 재설명 후 재출제 | 오답, `explanation_version < 3` |
| `end` | 세션 강제 종료 | 오답, `explanation_version >= 3` |

**관련 테이블** (단일 트랜잭션):
- `learning_sessions.status` (갱신)
- `learning_sessions.explanation_version` (오답 시 증가)
- `learning_records` (UPSERT: attempt_count, correct_count, mastery_score, last_reviewed_at, next_review_at)
- `weak_points` (오답 시: UPSERT, error_count 증가)
- `last_session` (UPSERT)

**메모**:
- `next_action = 'retry'`: 클라이언트는 `/explanation` 재호출 → 새 설명 로드.
- `next_action = 'end'`: 클라이언트는 `/recommendations/learning-path` 호출.

---

## 9. 이어하기 API

### 9-1. `GET /api/v1/learning/resume`

현재 사용자의 마지막 학습 지점을 조회합니다.

**인증**: 회원

**응답 (200)** — `last_session`이 있을 때:

```json
{
  "has_resume": true,
  "last_session": {
    "learning_session_id": "learn-uuid",
    "grammar_point_id": "grammar_n5_011",
    "level": "N5",
    "updated_at": "2026-04-19T11:00:00Z"
  }
}
```

**응답 (200)** — 없을 때 (신규 사용자):

```json
{
  "has_resume": false,
  "suggested_start_point": {
    "grammar_point_id": "grammar_n5_011",
    "level": "N5",
    "reason": "diagnosis_weak"
  }
}
```

**관련 테이블**:
- `last_session` (조회)
- `weak_points` (fallback 추천용)

---

## 10. 구현 체크리스트

각 API 구현 시 반드시 확인할 항목입니다.

### 공통
- [ ] Pydantic 스키마로 request/response 모델 정의
- [ ] 에러는 3-2 포맷 준수
- [ ] 인증 미들웨어로 access control
- [ ] 모든 DB 쓰기는 트랜잭션 내 처리

### 진단 API (6장)
- [ ] 익명 세션 만료 체크
- [ ] 답안 중복 제출 방어 (`UNIQUE` 제약 활용)
- [ ] 완료된 세션 재완료 방어 (409)
- [ ] `diagnosed_level` 계산 로직 테스트

### 링크 API (5-2)
- [ ] 단일 트랜잭션으로 5단계 처리
- [ ] `weak_points` 중복 생성 방어 (UPSERT)
- [ ] 이미 연결된 세션 재연결 방어 (409)

### 학습 API (8장)
- [ ] `explanation_version` 증가 로직
- [ ] 3회 오답 시 `end` 분기
- [ ] `mastery_score` 계산식 일관성
- [ ] LLM 캐시 히트율 로깅
- [ ] `last_session` UPSERT 정확성

### 추천 API (7장)
- [ ] 규칙 기반으로 결정적 (같은 입력 → 같은 출력)
- [ ] `limit` 파라미터 유효성 검증

---

## 미결 및 상태 (임시)
> 향후 `projectState.json`으로 이전 예정

- **진단 문제 저장소 확정**: DB 테이블 vs JSON seed 파일 (담당: 재현)
- **인증 토큰 포맷**: JWT vs 세션 쿠키 (담당: 재현 + 민석)
- **문제 생성 방식 Phase 2**: LLM 보조 여부 (담당: 재현)
- **`diagnosed_level` 계산 규칙**: 점수 구간별 매핑표 (담당: 재현 + 민석)
- **LLM 스트리밍 지원 여부**: Phase 2 이후 검토 (담당: 재현)
- **rate limiting 정책**: Phase 1 도입 여부 (담당: 재현)
