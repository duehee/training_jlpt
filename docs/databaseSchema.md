# 데이터베이스 스키마

> 최종 업데이트: 2026-04-19
> 담당 축: **How-internal** — 데이터를 어떻게 저장하는가
> 관련 문서: `serviceFlows.md`, `apiEndpoints.md`, `decisionLog.md`

---

## 📌 빠른 참조 (에이전트용)

**이 문서에서 찾을 수 있는 것**
- PostgreSQL 버전 및 필수 extension → 1장
- 공통 규칙 (PK, 시간, enum 등) → 2장
- 전체 테이블 목록 (익명/회원 구간) → 3장
- **익명 → 로그인 데이터 승계 구현** → 4장
- 테이블별 컬럼 정의 → 5장 ~ 14장
  - `users` → 5장
  - `anonymous_sessions` → 6장
  - `diagnostic_sessions` → 7장
  - `diagnostic_answers` → 8장
  - `learning_sessions` → 9장
  - `learning_records` → 10장
  - `weak_points` → 11장
  - `last_session` → 12장
  - `grammar_chunks` → 13장
  - `llm_response_cache` → 14장
- **청크 JSON 구조 표준** → 15장
- 인덱스 권장안 → 16장
- 마이그레이션 순서 → 17장

**이 문서에서 찾을 수 없는 것**
- 사용자 관점 플로우 → `serviceFlows.md`
- API 엔드포인트 → `apiEndpoints.md`
- 구현 순서 → `implementationRoadmap.md`
- 설계 결정의 배경 → `decisionLog.md`

---

## 이 문서는
PostgreSQL 16 + pgvector 기반의 **데이터베이스 스키마 참조**입니다.
모든 테이블 정의, 컬럼 타입, 제약, 인덱스, 청크 JSON 구조의 단일 진실 원천입니다.

**구현 관점 기준 문서**로, 사용자 플로우는 `serviceFlows.md`를 먼저 보세요.

---

## 1. 기본 설정

### 1-1. 버전
- **PostgreSQL 16**
- **pgvector** (PostgreSQL extension)

### 1-2. 필수 extension

```sql
CREATE EXTENSION IF NOT EXISTS vector;    -- pgvector
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- UUID 생성 등
```

### 1-3. Docker Compose 이미지
```yaml
# docker-compose.yml 일부
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: jlpt_agent
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
```

---

## 2. 공통 규칙

모든 테이블에 공통으로 적용되는 설계 원칙입니다.

| 규칙 | 내용 |
|------|------|
| PK | `UUID` (이유: 외부 노출 안전, 분산 생성 가능) |
| 시간 컬럼 | `TIMESTAMP WITH TIME ZONE` (TIMESTAMPTZ) |
| 유연 데이터 | `JSONB` (문자열 검색, 인덱스 가능) |
| 문자열 enum | DB enum 대신 `VARCHAR` + 애플리케이션 검증 (변경 유연성) |
| 생성/수정 시각 | `created_at`, `updated_at` 모두 NOT NULL |
| 삭제 정책 | Phase 1은 논리 삭제 최소화. 필요 시 `is_active BOOLEAN` 추가 |
| 네이밍 | 테이블/컬럼 모두 `snake_case` |

---

## 3. 전체 테이블 목록

Phase 1에서 사용하는 10개 테이블입니다. **익명/회원 구간이 명확히 분리**됩니다.

### 익명 구간 (로그인 전 진단 전용)
| # | 테이블 | 용도 |
|---|--------|------|
| 1 | `anonymous_sessions` | 익명 세션 임시 상태 |
| 2 | `diagnostic_sessions` | 진단 테스트 세션 |
| 3 | `diagnostic_answers` | 진단 문항별 답안 |

### 회원 구간 (로그인 이후)
| # | 테이블 | 용도 |
|---|--------|------|
| 4 | `users` | 회원 기준 정보 |
| 5 | `learning_sessions` | 학습 세션 |
| 6 | `learning_records` | 문법 포인트별 누적 학습 이력 |
| 7 | `weak_points` | 사용자 취약 문법 누적 |
| 8 | `last_session` | 이어하기 상태 |

### 공용 리소스
| # | 테이블 | 용도 |
|---|--------|------|
| 9 | `grammar_chunks` | 문법/비교 청크 원본 + 임베딩 |
| 10 | `llm_response_cache` | LLM 응답 캐시 |

---

## 4. 익명 → 로그인 데이터 승계

온보딩에서 **가장 설계가 까다로운 부분**입니다.
익명 진단 결과를 로그인 후에 어떻게 승계할지를 정의합니다.

### 4-1. 기본 원칙

**익명 데이터는 학습 도메인에 직접 섞지 않는다.**

- 익명 구간 테이블: `anonymous_sessions`, `diagnostic_sessions`, `diagnostic_answers`
- 회원 구간 테이블: `users`, `learning_sessions`, `learning_records`, `weak_points`, `last_session`
- 연결 고리: 
  - `anonymous_sessions.linked_user_id` → `users.id`
  - `users.initial_diagnostic_session_id` → `diagnostic_sessions.id`

### 4-2. 왜 이렇게 분리하는가

기존 대안(단일 테이블에 `user_id`와 `anonymous_session_id`를 동시에 받는 구조)은 아래 문제가 있습니다.

| 문제 | 구체적 영향 |
|------|------------|
| 경계 모호 | 어떤 데이터가 익명/회원 상태인지 쿼리로 판단 어려움 |
| 병합 복잡 | 로그인 시 익명 학습 데이터를 어떻게 병합할지 규칙이 복잡 |
| 기준 불일치 | 추천/복습/이어하기 기준을 통일하기 어려움 |
| 제약 표현 | DB 레벨 제약과 애플리케이션 로직이 모두 복잡해짐 |

분리 구조의 장점:
- 익명은 **진단 전용**으로 제한
- 학습 관련 데이터는 모두 `user_id`로 일원화
- 약점 분석/추천/복습 로직이 단순
- 로그인 이후 상태 추적이 안정적

### 4-3. 로그인 전 (익명 구간)

```text
1. anonymous_sessions 생성
   - session_token 발급
   - expires_at 설정 (기본 24시간)

2. diagnostic_sessions 시작
   - anonymous_session_id 연결
   - status = 'started'

3. diagnostic_answers 순차 저장
   - 문항별 정오답 기록

4. 진단 완료 처리
   - diagnostic_sessions.diagnosed_level 계산
   - diagnostic_sessions.score 계산
   - diagnostic_sessions.status = 'completed'
   - anonymous_sessions.diagnostic_completed_at 갱신
```

이 시점까지는 **모든 데이터가 `user_id` 없이** 존재합니다.

### 4-4. 로그인/가입 시점 (핵심 트랜잭션)

하나의 트랜잭션으로 아래 작업을 처리합니다.

```python
# 의사코드
with db.transaction():
    # Step 1: 사용자 레코드 처리
    user = create_or_get_user(email_or_nickname)
    
    # Step 2: 익명 세션 연결
    anonymous_session.linked_user_id = user.id
    anonymous_session.save()
    
    # Step 3: 사용자에 진단 세션 연결
    user.initial_diagnostic_session_id = diagnostic_session.id
    user.current_level = diagnostic_session.diagnosed_level
    user.save()
    
    # Step 4: 진단 결과 → weak_points 생성
    wrong_answers = diagnostic_answers.filter(
        diagnostic_session_id=diagnostic_session.id,
        is_correct=False
    )
    
    # grammar_point_id 기준 집계
    error_counts = aggregate_by_grammar_point(wrong_answers)
    
    for grammar_point_id, error_count in error_counts.items():
        WeakPoint.create(
            user_id=user.id,
            grammar_point_id=grammar_point_id,
            source='diagnosis',
            error_count=error_count,
            identified_at=now(),
        )
    
    # Step 5: 추천 시작 포인트 계산 (다음 스프린트에서 반환)
    # ORDER BY error_count DESC LIMIT 1
```


### 4-5. 로그인 후 (회원 구간)

- 학습은 `user_id` 기준으로만 진행
- `anonymous_sessions`는 더 이상 **쓰기에 참여하지 않음** (읽기 전용 히스토리)
- TTL 만료 시 cleanup job으로 삭제 가능 (`expires_at` 기준)

### 4-6. 예외 처리

| 상황 | 처리 |
|------|------|
| 진단 중 페이지 이탈 | `anonymous_sessions.expires_at`까지 복귀 가능 |
| 진단 없이 가입 | `users.initial_diagnostic_session_id = NULL`, 최초 학습 전 진단 유도 |
| 재진단 요청 | 새 `diagnostic_session`을 `user_id` 연결로 생성 (Phase 2 이후 검토) |
| 익명 세션 만료 후 가입 시도 | 진단 결과 소실. 재진단 유도 |

### 4-7. 관련 API 엔드포인트

구체적인 API 계약은 `apiEndpoints.md` 참조.

| API | 용도 |
|-----|------|
| `POST /api/v1/sessions/anonymous` | 익명 세션 생성 |
| `POST /api/v1/diagnosis/sessions` | 진단 세션 시작 |
| `POST /api/v1/diagnosis/sessions/{id}/complete` | 진단 완료 및 결과 계산 |
| `POST /api/v1/auth/link-session` | **로그인 시 승계 트랜잭션 실행** |

---

## 5. `users`

**목적**: 로그인 사용자의 기준 정보 저장.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | `UUID` | PK, DEFAULT `gen_random_uuid()` | 사용자 식별자 |
| `nickname` | `VARCHAR(50)` | NOT NULL | 표시 이름 |
| `email` | `VARCHAR(255)` | NULL, UNIQUE | 로그인/인증용 (Phase 1 선택) |
| `current_level` | `VARCHAR(10)` | NULL | 현재 추정 레벨 (N5~N1) |
| `target_level` | `VARCHAR(10)` | NULL | 목표 레벨 |
| `initial_diagnostic_session_id` | `UUID` | NULL, FK → `diagnostic_sessions.id` | 최초 진단 세션 연결 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | 생성 시각 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | 수정 시각 |

### 메모
- `initial_diagnostic_session_id`는 "익명 진단 후 가입" 추적용.
- Phase 1은 간이 로그인(닉네임) 가능. Phase 2 이상에서 이메일 필수화 검토.
- 향후 추가 후보: `onboarding_status`, `last_login_at`, `preferred_locale`.

---

## 6. `anonymous_sessions`

**목적**: 비로그인 사용자의 진단 흐름과 임시 상태 관리.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | `UUID` | PK | 익명 세션 식별자 |
| `session_token` | `VARCHAR(255)` | NOT NULL, UNIQUE | 외부 노출용 세션 토큰 |
| `linked_user_id` | `UUID` | NULL, FK → `users.id` | 로그인 후 연결된 사용자 |
| `diagnostic_completed_at` | `TIMESTAMPTZ` | NULL | 진단 완료 시각 |
| `expires_at` | `TIMESTAMPTZ` | NOT NULL | 만료 시각 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | 생성 시각 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | 수정 시각 |

### 메모
- **책임 범위**: 진단용 임시 상태까지만. 학습 상태는 포함하지 않음.
- 로그인 후 `linked_user_id` 갱신으로 계정 연결 추적.
- `expires_at` 기본값: 생성 시각 + 24시간 (애플리케이션 설정).

---

## 7. `diagnostic_sessions`

**목적**: 익명 사용자의 한 번의 진단 흐름 저장.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | `UUID` | PK | 진단 세션 식별자 |
| `anonymous_session_id` | `UUID` | NOT NULL, FK → `anonymous_sessions.id` | 익명 세션 연결 |
| `mode` | `VARCHAR(50)` | NOT NULL | `initial_assessment` 등 |
| `diagnosed_level` | `VARCHAR(10)` | NULL | 진단 완료 후 저장 |
| `score` | `INTEGER` | NULL | 획득 점수 |
| `max_score` | `INTEGER` | NOT NULL | 총점 |
| `status` | `VARCHAR(30)` | NOT NULL | `started`, `in_progress`, `completed`, `abandoned` |
| `started_at` | `TIMESTAMPTZ` | NOT NULL | 시작 시각 |
| `completed_at` | `TIMESTAMPTZ` | NULL | 종료 시각 |

### 메모
- **중요**: `user_id` 컬럼을 **두지 않습니다.** 진단은 익명 전용 흐름.
- 로그인 후에는 `users.initial_diagnostic_session_id`로 역참조.
- `mode`는 향후 재진단, 테마별 진단 등을 대비한 구분자.

---

## 8. `diagnostic_answers`

**목적**: 진단 문제별 사용자 답안 저장.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | `UUID` | PK | 답안 식별자 |
| `diagnostic_session_id` | `UUID` | NOT NULL, FK → `diagnostic_sessions.id` | 소속 진단 세션 |
| `question_id` | `VARCHAR(100)` | NOT NULL | 문제 식별자 |
| `grammar_point_id` | `VARCHAR(100)` | NOT NULL | 연결 문법 포인트 |
| `selected_choice` | `VARCHAR(255)` | NOT NULL | 사용자가 고른 선택지 |
| `correct_choice` | `VARCHAR(255)` | NOT NULL | 정답 선택지 |
| `is_correct` | `BOOLEAN` | NOT NULL | 정오답 여부 |
| `time_spent_sec` | `INTEGER` | NULL | 소요 시간 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | 제출 시각 |

### 추가 제약
- `UNIQUE (diagnostic_session_id, question_id)` — 같은 세션 내 중복 답안 방지.

### 메모
- 진단 결과 복기 + 약점 계산의 원본 데이터.
- 로그인 후 `weak_points` 생성 시 이 테이블이 핵심 입력.
- `question_id`는 문제 seed 데이터의 키와 일치해야 함.

---

## 9. `learning_sessions`

**목적**: 로그인 이후 한 번의 문법 학습 흐름 저장.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | `UUID` | PK | 학습 세션 식별자 |
| `user_id` | `UUID` | NOT NULL, FK → `users.id` | 로그인 사용자 연결 |
| `grammar_point_id` | `VARCHAR(100)` | NOT NULL | 현재 학습 문법 |
| `level` | `VARCHAR(10)` | NOT NULL | N5~N1 |
| `status` | `VARCHAR(30)` | NOT NULL | `started`, `in_progress`, `retrying`, `completed` |
| `explanation_version` | `INTEGER` | NOT NULL, DEFAULT `1` | 재설명 횟수 추적 |
| `started_at` | `TIMESTAMPTZ` | NOT NULL | 시작 시각 |
| `completed_at` | `TIMESTAMPTZ` | NULL | 종료 시각 |

### 메모
- `anonymous_session_id`는 **없습니다.** 학습은 로그인 이후만 허용.
- `explanation_version`이 2 이상이면 재설명 경로를 거친 것.
- 오answer 3회 후 `status = 'completed'`로 강제 종료 (serviceFlows.md 2장 참조).

---

## 10. `learning_records`

**목적**: 문법 포인트 단위의 누적 학습 이력 저장.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | `UUID` | PK | 학습 기록 식별자 |
| `user_id` | `UUID` | NOT NULL, FK → `users.id` | 사용자 식별자 |
| `grammar_point_id` | `VARCHAR(100)` | NOT NULL | 문법 포인트 |
| `level` | `VARCHAR(10)` | NOT NULL | 레벨 |
| `attempt_count` | `INTEGER` | NOT NULL, DEFAULT `0` | 총 시도 횟수 |
| `correct_count` | `INTEGER` | NOT NULL, DEFAULT `0` | 정답 횟수 |
| `mastery_score` | `NUMERIC(4,3)` | NOT NULL, DEFAULT `0.0` | 숙련도 (0.000 ~ 1.000) |
| `last_result` | `VARCHAR(30)` | NOT NULL | `correct`, `incorrect`, `retry_correct` |
| `last_reviewed_at` | `TIMESTAMPTZ` | NOT NULL | 마지막 학습 시각 |
| `next_review_at` | `TIMESTAMPTZ` | NULL | 다음 복습 시각 (간격 반복) |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | 생성 시각 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | 수정 시각 |

### 추가 제약
- `UNIQUE (user_id, grammar_point_id)` — 사용자 × 문법 포인트는 1:1.

### 메모
- 추천 로직과 복습 스케줄링의 기준 테이블.
- `mastery_score` 계산식: 애플리케이션 레이어에서 결정 (초기 안: `correct_count / attempt_count` 기반 EMA).

---

## 11. `weak_points`

**목적**: 로그인 사용자 기준 취약 문법 포인트 누적 관리.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | `UUID` | PK | 약점 식별자 |
| `user_id` | `UUID` | NOT NULL, FK → `users.id` | 로그인 사용자 연결 |
| `grammar_point_id` | `VARCHAR(100)` | NOT NULL | 취약 문법 포인트 |
| `source` | `VARCHAR(50)` | NOT NULL | `diagnosis`, `learning` |
| `error_count` | `INTEGER` | NOT NULL, DEFAULT `0` | 누적 오류 횟수 |
| `metadata` | `JSONB` | NULL | 패턴 정보, 원인 보조 정보 |
| `identified_at` | `TIMESTAMPTZ` | NOT NULL | 최초 식별 시각 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | 최신 갱신 시각 |

### 추가 제약
- `UNIQUE (user_id, grammar_point_id)` — 사용자 × 문법 포인트 1:1 (기존 레코드 갱신).

### 메모
- 생성 시점: 로그인 직후 진단 결과로 최초 생성 → 이후 오답 발생 시 갱신 (4장 참조).
- `source`로 약점 발견 경로 추적 (진단 기반 / 학습 기반).
- `metadata` 예시: `{"patterns": ["조사 혼동"], "triggered_by": ["N5_grammar_012"]}`.

---

## 12. `last_session`

**목적**: 재방문 시 이어하기 상태 저장.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | `UUID` | PK | 상태 식별자 |
| `user_id` | `UUID` | NOT NULL, UNIQUE, FK → `users.id` | 사용자별 한 건 유지 |
| `learning_session_id` | `UUID` | NOT NULL, FK → `learning_sessions.id` | 마지막 학습 세션 |
| `grammar_point_id` | `VARCHAR(100)` | NOT NULL | 마지막 문법 포인트 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | 최근 갱신 시각 |

### 메모
- 사용자당 1건만 존재 (`user_id UNIQUE`).
- 새 학습 세션 시작 시 UPSERT로 갱신.

---

## 13. `grammar_chunks` ⭐ 핵심 테이블

**목적**: 문법 포인트 및 비교 문법 청크를 저장하는 retrieval 원본 + 임베딩 테이블.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | `UUID` | PK | 청크 식별자 |
| `chunk_serial` | `VARCHAR(50)` | NOT NULL, UNIQUE | 시리얼 (`N5_grammar_001`) |
| `grammar_point_id` | `VARCHAR(100)` | NOT NULL | 문법 포인트 식별자 |
| `level` | `VARCHAR(10)` | NOT NULL | `N5`, `N4`, `N3` |
| `chunk_type` | `VARCHAR(20)` | NOT NULL | `grammar`, `compare` |
| `border_flag` | `BOOLEAN` | NOT NULL, DEFAULT `FALSE` | 레벨 경계 문법 여부 |
| `content` | `JSONB` | NOT NULL | 청크 본문 (타입별 구조: 15장 참조) |
| `embedding_text` | `TEXT` | NOT NULL | 임베딩 대상 텍스트 |
| `embedding` | `VECTOR(1536)` | NULL | pgvector 임베딩 (text-embedding-3-small) |
| `source_status` | `VARCHAR(30)` | NOT NULL, DEFAULT `'draft'` | `draft`, `validated`, `published` |
| `metadata` | `JSONB` | NULL | 기타 retrieval용 메타데이터 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | 생성 시각 |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | 수정 시각 |

### 핵심 설계 근거

**왜 `content JSONB`인가**
- 청크 타입(grammar vs compare)별로 필드 구조가 다름
- 스키마 변경 없이 필드 추가 가능 (마이그레이션 부담 감소)
- 검색 최적화 컬럼(`embedding_text`, `embedding`)만 top-level에 두어 인덱스 가능

**왜 `border_flag`가 top-level인가**
- N5~N4 경계 문법을 자주 필터링 (예: N5 기본만 보여주기 vs 전체)
- top-level 컬럼이어야 인덱스 효율이 좋음

**왜 `embedding`과 `embedding_text`를 분리하는가**
- `embedding_text`는 임베딩 생성 시 입력된 원문 (디버깅/재임베딩용)
- `embedding`은 실제 벡터 (검색용)
- 재임베딩 시 `embedding_text` 변경 여부로 판단 가능

**왜 `chunk_serial`과 `id`가 분리되는가**
- `id` UUID: 시스템 내부 참조용, 변경 불가
- `chunk_serial`: 사람이 읽을 수 있는 식별자 (`N5_grammar_001`), 관리/디버깅용

### 동기화 흐름
```text
PG에서 content 업데이트 시:
  1. embedding_text 변경 감지
  2. 새 embedding 생성 (OpenAI API 호출)
  3. 같은 row의 embedding 컬럼 UPDATE
  4. 단일 트랜잭션으로 처리

→ 별도 벡터 저장소 없음. 동기화 문제 원천 제거.
```

---

## 14. `llm_response_cache`

**목적**: LLM 응답 캐싱으로 API 비용 절감.

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | `UUID` | PK | 캐시 식별자 |
| `cache_key` | `VARCHAR(255)` | NOT NULL, UNIQUE | 캐시 키 (프롬프트 해시 + 모델) |
| `prompt_hash` | `VARCHAR(64)` | NOT NULL | 프롬프트 SHA-256 해시 |
| `model_name` | `VARCHAR(100)` | NOT NULL | 사용 모델 (`gpt-4o-mini` 등) |
| `response_text` | `TEXT` | NOT NULL | 응답 본문 |
| `token_usage` | `JSONB` | NULL | `{"prompt": N, "completion": N, "total": N}` |
| `expires_at` | `TIMESTAMPTZ` | NULL | 만료 시각 |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | 생성 시각 |

### 메모
- `cache_key` 생성 규칙: `f"{model_name}:{prompt_hash}"`
- 같은 프롬프트 + 다른 모델 = 다른 캐시 (모델 버전 차이 고려).
- Phase 1은 TTL 단순 운영. Phase 3 이후 더 정교한 캐시 전략 검토.

---

## 15. 청크 JSON 구조 표준 ⭐

`grammar_chunks.content` JSONB 필드의 **청크 타입별 표준 구조**입니다.

### 15-1. 문법 청크 (`chunk_type = 'grammar'`)

```json
{
  "point": "は",
  "meaning_ko": "문장의 주제를 제시하는 조사. ~은/는에 해당.",
  "connection": "명사 + は\n예) 私は学生です\n※ BORDER: 대조 용법은 비교 청크에서 심화",
  "examples": [
    { "jp": "私は学生です。", "ko": "저는 학생입니다." },
    { "jp": "今日は寒いです。", "ko": "오늘은 춥습니다." }
  ],
  "related_grammar": ["が", "も"],
  "common_mistakes": "신정보 제시 상황에서 は를 써야 할 자리에 が를 쓰는 경우가 많다",
  "nuance": "기지 정보·공유 정보를 화제로 올릴 때 사용",
  "tags": ["조사", "주제", "기초"],
  "difficulty": 1,
  "source": "jlptsensei.com 목록 참고, 설명 LLM 생성"
}
```

#### 필드 설명
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `point` | string | ✅ | 문법 포인트 (일본어 원문) |
| `meaning_ko` | string | ✅ | 한국어 의미 설명 |
| `connection` | string | ✅ | 접속 규칙 |
| `examples` | array | ✅ | 예문 2~3개 (`jp`, `ko` 키) |
| `related_grammar` | array | ⭕ | 관련/혼동 문법 포인트 배열 |
| `common_mistakes` | string | ⭕ | 자주 하는 실수 |
| `nuance` | string | ⭕ | 뉘앙스 보충 설명 |
| `tags` | array | ⭕ | 검색/분류용 태그 |
| `difficulty` | integer | ⭕ | 난이도 (1~5) |
| `source` | string | ⭕ | 출처 정보 |

### 15-2. 비교 청크 (`chunk_type = 'compare'`)

```json
{
  "pair": ["は", "が"],
  "confusion_point": "주제 표시 vs 주어 강조",
  "examples": [
    {
      "case": "は 사용",
      "jp": "私は学生です。",
      "ko": "저는 학생입니다."
    },
    {
      "case": "が 사용",
      "jp": "私が学生です。",
      "ko": "제가 학생입니다. (강조)"
    }
  ],
  "common_mistakes": "신정보 제시 상황에서 は를 써야 할 자리에 が를 쓰는 경우가 많다",
  "explanation_ko": "は는 이미 아는 정보(주제)를 제시할 때, が는 새로운 정보나 강조 대상을 제시할 때 씁니다.",
  "tags": ["조사", "혼동", "기초"]
}
```

#### 필드 설명
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `pair` | array(2) | ✅ | 비교 대상 문법 2개 (가나 순 정렬) |
| `confusion_point` | string | ✅ | 혼동 포인트 한 줄 요약 |
| `examples` | array | ✅ | 각 케이스별 예문 (`case`, `jp`, `ko`) |
| `common_mistakes` | string | ⭕ | 자주 하는 실수 |
| `explanation_ko` | string | ✅ | 한국어 핵심 설명 |
| `tags` | array | ⭕ | 검색/분류용 태그 |

### 15-3. `embedding_text` 작성 기준

`grammar_chunks.embedding_text` 필드의 작성 규칙입니다.

| 기준 | 내용 |
|------|------|
| 언어 | **한국어 중심** (쿼리가 한국어로 유입되므로) |
| 문법명 표기 | 일본어 원문 유지 (크로스링구얼 매칭 보조) |
| 길이 | **40~80자** 권장 |
| 포함 요소 | ① 문법 포인트명 ② 핵심 의미 ③ 혼동 대상 ④ 레벨/용법 키워드 |
| 금지 | 예문 전체 복사, 접속 규칙 상세 나열 |

#### 예시
"は 주제조사: 문장의 화제 설정. 공유 정보에 사용. が(신정보·강조)와 혼동 주의."

---

## 16. 인덱스 권장안

### 16-1. 초기 필수 인덱스
Phase 1 초기 마이그레이션에 포함해야 할 인덱스입니다.

```sql
-- 익명/진단
CREATE INDEX idx_anon_sessions_token ON anonymous_sessions(session_token);
CREATE INDEX idx_anon_sessions_linked_user ON anonymous_sessions(linked_user_id);
CREATE INDEX idx_diag_sessions_anon ON diagnostic_sessions(anonymous_session_id);
CREATE INDEX idx_diag_answers_session ON diagnostic_answers(diagnostic_session_id);

-- 학습
CREATE INDEX idx_learning_sessions_user ON learning_sessions(user_id);
CREATE INDEX idx_learning_records_user_gp 
  ON learning_records(user_id, grammar_point_id);
CREATE INDEX idx_weak_points_user_gp 
  ON weak_points(user_id, grammar_point_id);
CREATE INDEX idx_last_session_user ON last_session(user_id);

-- 청크
CREATE INDEX idx_chunks_level ON grammar_chunks(level);
CREATE INDEX idx_chunks_type ON grammar_chunks(chunk_type);
CREATE INDEX idx_chunks_gp ON grammar_chunks(grammar_point_id);
CREATE INDEX idx_chunks_border ON grammar_chunks(border_flag);
CREATE INDEX idx_chunks_source_status ON grammar_chunks(source_status);

-- 복합 인덱스 (retrieval 최적화)
CREATE INDEX idx_chunks_gp_level_type 
  ON grammar_chunks(grammar_point_id, level, chunk_type);

-- 캐시
CREATE INDEX idx_llm_cache_key ON llm_response_cache(cache_key);
```

### 16-2. 벡터 인덱스

Phase 1 후반, 청크 수량이 100개 이상 확보된 후 추가:

```sql
-- IVFFlat (추천, 삽입/업데이트 빈도 낮을 때)
CREATE INDEX idx_chunks_embedding 
  ON grammar_chunks 
  USING ivfflat (embedding vector_cosine_ops) 
  WITH (lists = 100);

-- 또는 HNSW (추천, 쿼리 성능 우선 시)
-- CREATE INDEX idx_chunks_embedding
--   ON grammar_chunks
--   USING hnsw (embedding vector_cosine_ops);
```

#### 선택 기준
- **IVFFlat**: 인덱스 생성 빠름, 쿼리 성능 중간. 현재 규모(~400개)에 적합.
- **HNSW**: 쿼리 성능 우수, 인덱스 생성 느림, 메모리 많이 사용. 대규모용.

→ Phase 1은 IVFFlat 권장, Phase 3에서 데이터 규모 따라 재검토.

### 16-3. 추가 고려 인덱스 (Phase 1 후반)

```sql
-- 추천 로직 최적화
CREATE INDEX idx_weak_points_user_error 
  ON weak_points(user_id, error_count DESC);

-- 복습 스케줄러
CREATE INDEX idx_learning_records_next_review 
  ON learning_records(next_review_at) 
  WHERE next_review_at IS NOT NULL;
```

---

## 17. 마이그레이션 순서

Alembic 기반 단계별 마이그레이션 권장 순서입니다.

### 17-1. Migration 1: 기반 + 익명 구간
```text
1. vector, pgcrypto extension 생성
2. anonymous_sessions
3. diagnostic_sessions (anonymous_sessions FK)
4. diagnostic_answers (diagnostic_sessions FK)
```

### 17-2. Migration 2: 회원 구간
```text
1. users (diagnostic_sessions FK 순환 참조 주의)
2. learning_sessions
3. learning_records (UNIQUE constraint)
4. last_session
```

### 17-3. Migration 3: 콘텐츠 + 캐시
```text
1. grammar_chunks (embedding은 VECTOR(1536))
2. llm_response_cache
```

### 17-4. Migration 4: 약점 + 인덱스
```text
1. weak_points
2. 초기 필수 인덱스 일괄 생성 (16-1장)
```

### 17-5. Migration 5 (후속): 벡터 인덱스
```text
1. grammar_chunks.embedding 데이터 확보 후
2. IVFFlat 인덱스 생성 (16-2장)
```

### 참고 사항
- `users`와 `diagnostic_sessions` 간 **순환 FK**가 있어, 한쪽을 먼저 만들고 ALTER TABLE로 FK 추가하는 것이 안전.
- 각 마이그레이션은 **독립적으로 롤백 가능**한 단위로 구성.
- 초기 데이터 seed는 마이그레이션이 아닌 **별도 스크립트** (`src/scripts/`) 로 관리.

---

## 미결 및 상태 (임시)
> 향후 `projectState.json`으로 이전 예정

- **`grammar_point_id` 포맷 규칙 최종 확정**: 예) `grammar_n5_001` vs `gp_n5_001` (담당: 수진 + 재현)
- **진단 문제 저장소**: DB 테이블화 여부 (담당: 재현)
- **`mastery_score` 계산식 확정**: EMA vs 단순 비율 vs 다른 방식 (담당: 재현)
- **`weak_points.metadata` JSONB 스키마 표준화**: 패턴 키 구조 (담당: 수진 + 재현)
- **벡터 인덱스 최종 선택**: IVFFlat vs HNSW (데이터 규모 확보 후 결정)
- **`llm_response_cache` TTL 기본값**: 설명은 무한? 문제는 1주? (담당: 재현)
- **진단 score → diagnosed_level 매핑 규칙**: 점수 구간별 레벨 판정 (담당: 재현 + 민석)