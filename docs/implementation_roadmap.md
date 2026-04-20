# 구현 로드맵

> 최종 업데이트: 2026-04-19
> 담당 축: **When** — 무엇을 어떤 순서로 구현하는가
> 관련 문서: `service_flows.md`, `database_schema.md`, `api_endpoints.md`

---

## 📌 빠른 참조 (에이전트용)

**이 문서에서 찾을 수 있는 것**
- Phase 1 구현 목표 → 1장
- 개발 방향 원칙 → 2장
- 저장소 디렉토리 골격 → 3장
- Stage 0 ~ 5 상세 → 4장 ~ 9장
  - Stage 0: 기반 골격 → 4장
  - Stage 1: 진단 수직 슬라이스 → 5장
  - Stage 2: 학습 코어 → 6장
  - Stage 3: Retrieval 및 임베딩 → 7장
  - Stage 4: LangGraph 통합 → 8장
  - Stage 5: 데모 UI → 9장
- 핸드오프 산출물 표준 → 10장
- 초기 결정 필요 항목 → 11장

**이 문서에서 찾을 수 없는 것**
- 사용자 플로우 → `service_flows.md`
- DB 스키마 → `database_schema.md`
- API 계약 → `api_endpoints.md`
- 확정된 의사결정 → `decision_log.md`
- 에이전트 협업 규칙 → `agent_guide.md`

---

## 이 문서는
JLPT 개인 학습 에이전트 **Phase 1 구현의 순서**와 **각 단계의 완료 기준**을 정의합니다.
"무엇부터 어떤 순서로 할 것인가"에 대한 단일 기준 문서입니다.

---

## 1. Phase 1 구현 목표

Phase 1이 끝났을 때 아래가 실제로 동작해야 합니다.

1. 사용자가 **익명으로 진단**을 완료할 수 있다.
2. **레벨 판정 + 약점 문법**이 계산된다.
3. 로그인 후 **진단 결과가 승계**된다.
4. **약점 기반 학습 포인트**가 추천된다.
5. **RAG 기반 문법 설명**이 제공된다.
6. 이해도 확인 문제에 답하면 **정오답 분기**가 동작한다.
7. 재방문 시 **이어하기**가 된다.

Phase 1은 "문서만 있는 상태"가 아니라 **"직접 돌려볼 수 있는 데모"**까지 가야 합니다.

---

## 2. 개발 방향 원칙

구현 순서의 핵심 원칙입니다.

### 2-1. 얇은 수직 슬라이스 우선
모든 레이어를 동시에 크게 벌리지 않습니다.
**"가장 얇지만 끝까지 이어지는 흐름"**을 먼저 만든 뒤, 그 위에 기능을 쌓습니다.

### 2-2. 기능 순서

```
기반 골격 (실행 가능 상태)
  ↓
진단 수직 슬라이스 (하드코딩 OK)
  ↓
학습 코어 (하드코딩 OK)
  ↓
Retrieval 대체 (하드코딩 → DB)
  ↓
LangGraph 통합 (분기 로직 그래프화)
  ↓
데모 UI
```

### 2-3. 단계별 완료 기준
각 Stage는 **"구체적 동작 확인 가능한 완료 기준"**을 가집니다.
테스트가 아니라 **실제 실행 결과**로 판단합니다.

---

## 3. 저장소 디렉토리 골격

```
training_jlpt/
├── src/
│   ├── api/
│   │   ├── main.py                  FastAPI 엔트리포인트
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── sessions.py          (anonymous, link)
│   │   │   ├── diagnosis.py
│   │   │   ├── recommendations.py
│   │   │   └── learning.py
│   │   ├── schemas/                 Pydantic 모델
│   │   └── dependencies/            인증/DB 세션 의존성
│   ├── core/
│   │   ├── config.py                환경변수, 설정
│   │   ├── logging.py
│   │   └── security.py              인증 유틸
│   ├── db/
│   │   ├── base.py                  SQLAlchemy base
│   │   ├── models/                  ORM 모델
│   │   ├── repositories/            DB 접근 레이어
│   │   └── migrations/              Alembic
│   ├── services/
│   │   ├── sessions.py
│   │   ├── diagnosis.py
│   │   ├── recommendations.py
│   │   ├── learning.py
│   │   ├── retrieval.py             pgvector 검색
│   │   ├── embeddings.py            OpenAI embedding
│   │   └── llm.py                   LLM 호출 + 캐싱
│   ├── agent/
│   │   ├── graph.py                 LangGraph 정의
│   │   ├── state.py                 학습 state 객체
│   │   └── nodes/                   retrieve/explain/quiz/branch
│   └── scripts/
│       ├── seed_diagnosis_questions.py
│       ├── import_grammar_chunks.py
│       └── embed_grammar_chunks.py
├── data/
│   ├── raw/                         원본 데이터
│   ├── curated/                     수진 검수 완료
│   └── generated/                   LLM 생성 결과
├── tests/
│   ├── api/
│   ├── services/
│   └── integration/
├── docs/
├── docker-compose.yml
├── pyproject.toml
└── projectState.json                (예정)
```

### 네이밍 참고
- 디렉토리/파일: `snake_case` (파이썬 관례)
- 단, `docs/` 하위 문서 파일명도 `snake_case` (문서 관례, `agent_guide.md` 참조)

---

## 4. Stage 0: 기반 골격

### 목표
저장소를 **실제 실행 가능한 상태**로 만든다.

### 범위
- [ ] `src/`, `tests/`, `data/` 디렉토리 생성
- [ ] `pyproject.toml` 구성 (Poetry)
- [ ] `docker-compose.yml` 작성
  - PostgreSQL 16 + pgvector 컨테이너
  - Redis 컨테이너
  - 앱 서비스 (개발 모드)
- [ ] FastAPI 앱 엔트리포인트 생성
- [ ] `.env` 기반 설정 로더 구현
- [ ] DB 연결 유틸 (`db/base.py`)
- [ ] Redis 클라이언트 유틸
- [ ] Alembic 초기화
- [ ] `GET /health` 엔드포인트

### 완료 기준

```
docker-compose up -d
curl http://localhost:8000/health
# → {"status": "ok", "version": "0.1.0"}
```

### 산출물
- `docker-compose.yml`
- `src/api/main.py` (FastAPI 앱)
- `src/core/config.py`
- `src/db/base.py`
- `alembic.ini` + 빈 마이그레이션 디렉토리

---

## 5. Stage 1: 진단 수직 슬라이스

### 목표
사용자가 처음 가치를 느끼는 **가장 작은 흐름**을 완성한다.
진단을 끝내고 레벨/약점을 받아볼 수 있는 상태.

### 범위
- [ ] Alembic Migration 1: 기반 + 익명 구간 (`database_schema.md` 17-1장)
- [ ] Alembic Migration 2: 회원 구간
- [ ] ORM 모델 작성 (`anonymous_sessions`, `diagnostic_*`, `users`)
- [ ] 진단 문제 seed 데이터 (최소 10문항)
- [ ] seed 스크립트: `src/scripts/seed_diagnosis_questions.py`
- [ ] API 구현 (`api_endpoints.md` 5, 6장):
  - [ ] `POST /api/v1/sessions/anonymous`
  - [ ] `POST /api/v1/diagnosis/sessions`
  - [ ] `GET /api/v1/diagnosis/sessions/{id}/questions`
  - [ ] `POST /api/v1/diagnosis/sessions/{id}/answers`
  - [ ] `POST /api/v1/diagnosis/sessions/{id}/complete`
  - [ ] `GET /api/v1/diagnosis/sessions/{id}/result`
  - [ ] `POST /api/v1/auth/link-session`
- [ ] `diagnosed_level` 계산 로직 (서비스 레이어)
- [ ] 약점 집계 로직 (링크 시점 트랜잭션)

### 완료 기준

```
# 1. 익명 세션 생성
curl -X POST /api/v1/sessions/anonymous
# 2. 진단 시작
# 3. 10문제 답안 제출
# 4. 진단 완료 → 레벨/약점 받기
# 5. 로그인 → weak_points 생성 확인
# 6. DB에서 users, weak_points 조회로 검증
```

### 의존성
- **재현**: 모든 구현
- **수진 → 재현 핸드오프**: 진단 문제 10문항 (`data/curated/diagnosis_questions.json`)
- **츠쿠야**: 진단 문항 문구 검수

---

## 6. Stage 2: 학습 코어

### 목표
약점 포인트에서 **실제 학습 세션으로 연결**.
이 시점까지는 문법 설명을 **하드코딩**해도 됨 (Stage 3에서 대체).

### 범위
- [ ] Alembic Migration 3: 콘텐츠 + 캐시
- [ ] Alembic Migration 4: 약점 + 인덱스
- [ ] ORM 모델 추가 (`learning_*`, `weak_points`, `last_session`, `grammar_chunks`, `llm_response_cache`)
- [ ] API 구현 (`api_endpoints.md` 7, 8, 9장):
  - [ ] `GET /api/v1/recommendations/learning-path`
  - [ ] `POST /api/v1/learning/sessions`
  - [ ] `GET /api/v1/learning/sessions/{id}`
  - [ ] `GET /api/v1/learning/sessions/{id}/explanation` (**하드코딩**)
  - [ ] `POST /api/v1/learning/sessions/{id}/question` (**하드코딩**)
  - [ ] `POST /api/v1/learning/sessions/{id}/answers`
  - [ ] `GET /api/v1/learning/resume`
- [ ] `mastery_score` 계산 로직
- [ ] 3회 오답 종료 분기
- [ ] `last_session` UPSERT

### 완료 기준
- 진단 완료 후 `/recommendations/learning-path` → 1개 이상 포인트 반환
- 학습 세션 생성 → 설명 (하드코딩) → 문제 → 답안 → 분기 전체 동작
- 오답 3회 시 `next_action: 'end'` 반환
- 재로그인 → `/learning/resume` → 마지막 지점 반환

### 의존성
- **재현**: 모든 구현
- Stage 1 완료 필수

---

## 7. Stage 3: Retrieval 및 임베딩 파이프라인

### 목표
하드코딩 설명을 **실제 retrieval 기반**으로 전환.

### 범위
- [ ] `grammar_chunks` 데이터 import 스크립트: `src/scripts/import_grammar_chunks.py`
- [ ] 임베딩 생성 스크립트: `src/scripts/embed_grammar_chunks.py`
  - OpenAI text-embedding-3-small 호출
  - 배치 처리 (비용 + 속도)
  - `embedding_text` 변경 시 재임베딩 로직
- [ ] `services/embeddings.py`: 임베딩 생성 추상화
- [ ] `services/retrieval.py`: pgvector 유사도 검색
  - `chunk_type` 필터링
  - `level` 필터링
  - `grammar_point_id` 필터링
- [ ] `services/llm.py`: LLM 호출 + `llm_response_cache` 활용
- [ ] `/learning/sessions/{id}/explanation` 하드코딩 제거 → 실제 RAG
- [ ] `/learning/sessions/{id}/question` 하드코딩 제거 → LLM 생성

### 완료 기준
- `grammar_chunks` 테이블에 N5 84개 로드됨
- 모든 청크에 `embedding` 컬럼 값 존재
- 벡터 인덱스 생성 (Migration 5)
- 문법 설명이 DB 청크 기반으로 반환됨 (하드코딩 아님)
- LLM 캐시 히트 시 `cached: true` 반환

### 의존성
- **수진 → 재현 핸드오프**: N5 문법 청크 JSON 완성 (`data/curated/n5_grammar_chunks.json`)
- **츠쿠야**: 청크 데이터 샘플링 검수
- **재현**: 임베딩 파이프라인 + RAG 구현

---

## 8. Stage 4: LangGraph 통합

### 목표
분기 로직을 서비스 코드에서 **명시적인 워크플로우**로 분리.

### 범위
- [ ] `agent/state.py`: 학습 state 객체 (LangGraph 호환)
- [ ] `agent/nodes/retrieve.py`: grammar + compare 청크 retrieval
- [ ] `agent/nodes/explain.py`: 설명 생성 (LLM + 캐시)
- [ ] `agent/nodes/quiz.py`: 확인 문제 생성
- [ ] `agent/nodes/branch.py`: 정오답 분기 로직
- [ ] `agent/graph.py`: 그래프 정의 (node 연결, edge)
- [ ] `/learning/sessions/{id}/*` 엔드포인트를 LangGraph 호출로 리팩토링
- [ ] 그래프 상태 추적 로깅

### 완료 기준
- 학습 루프가 **그래프 형태로 추적 가능**
- 같은 API 계약(`api_endpoints.md`)이 유지됨
- LangGraph 내부 리팩토링만으로 외부 계약 변화 없음

### 의존성
- Stage 3 완료 필수

---

## 9. Stage 5: 데모 UI

### 목표
외부인이 **직접 써볼 수 있는 MVP 화면**.

### 범위
- [ ] Streamlit 앱 골격 (`demo/app.py`)
- [ ] 화면 구현:
  - [ ] 온보딩 진입
  - [ ] 진단 테스트 UI
  - [ ] 진단 결과 UI
  - [ ] 로그인/가입 UI
  - [ ] 학습 포인트 추천 UI
  - [ ] 학습 세션 UI (설명 + 문제)
  - [ ] 이어하기 UI
- [ ] 백엔드 API 연동 (requests 라이브러리)
- [ ] 에러 처리

### 완료 기준
- `streamlit run demo/app.py`로 실행 가능
- 백엔드 코드를 읽지 않아도 전체 흐름 체험 가능
- 면접 시연 가능 수준

### 의존성
- Stage 4 완료 후 진행 권장 (API 안정화)

---

## 10. 핸드오프 산출물 표준

멀티 에이전트 협업은 **상태 업데이트만으로는 부족**합니다.
핸드오프는 반드시 **파일 또는 스키마** 형태로 끝나야 합니다.

| From → To | 산출물 경로 | 포맷 |
|-----------|-------------|------|
| 수진 → 재현 | `data/curated/n5_grammar_chunks.json` | JSON 배열 (15장 구조) |
| 수진 → 재현 | `data/curated/n5_compare_chunks.json` | JSON 배열 |
| 수진 → 재현 | `data/curated/diagnosis_questions.json` | JSON 배열 (seed용) |
| 츠쿠야 → 팀 | `docs/validation_checklist.md` | 마크다운 체크리스트 |
| 민석 → 팀 | `docs/decision_log.md` 업데이트 | 날짜별 항목 추가 |
| 재현 → 팀 | `src/db/models/`, `src/api/schemas/`, `alembic/versions/` | 코드 |
| 재현 → 수진 | `src/scripts/generate_chunks.py` | 배치 생성 스크립트 |

**파일 기반 산출물이 없으면 핸드오프는 완료되지 않은 것으로 간주**합니다.

---

## 11. 초기 결정 필요 항목

Stage 1 착수 전에 반드시 확정해야 할 항목입니다.

| # | 항목 | 담당 | 근거 문서 |
|---|------|------|----------|
| 1 | Phase 1 인증 방식 (닉네임 vs 이메일) | 민석 | `service_flows.md` 미결 |
| 2 | 익명 세션 저장소 (Redis vs PG vs 혼용) | 재현 | `database_schema.md` 미결 |
| 3 | `grammar_point_id` 포맷 | 수진 + 재현 | `database_schema.md` 미결 |
| 4 | 진단 문제 저장소 (DB vs JSON seed) | 재현 | `api_endpoints.md` 미결 |
| 5 | `diagnosed_level` 계산 규칙 | 재현 + 민석 | `api_endpoints.md` 미결 |
| 6 | 진단 점수 방식 (완전 규칙 vs LLM 보조) | 재현 + 민석 | - |

---

## 미결 및 상태 (임시)
> 향후 `projectState.json`으로 이전 예정

- **현재 단계**: Stage 0 착수 준비 (기술 스택 확정 완료, DB 스키마 확정 완료)
- **병목**: 재현의 배치 생성 스크립트 + 수진의 N5 데이터 완성
- **의존 관계**: Stage 1 진단 문제 seed (수진 핸드오프 대기)
- **Stage 6 후보 (Phase 1 마지막)**: 기본 eval 프레임워크 도입 여부