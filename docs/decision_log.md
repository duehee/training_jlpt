# 의사결정 로그

> 최종 업데이트: 2026-04-29
> 담당 축: **Decisions** — 무엇이 왜 확정되었는가
> 관련 문서: `product_overview.md`, `service_flows.md`, `database_schema.md`, `api_endpoints.md`

---

## 📌 빠른 참조 (에이전트용)

**이 문서에서 찾을 수 있는 것**
- 확정된 결정의 날짜별 기록
- 각 결정의 근거와 영향 범위
- 카테고리별 검색 (DATA / PROCESS / STACK / ARCH / DB / FLOW)

**이 문서에서 찾을 수 없는 것**
- 아직 결정되지 않은 이슈 → 각 문서의 **미결 및 상태** 섹션
- 현재 작업 상태 → `project_summary.md` + `planning/session_N/pm_minseok/summary.md`
- 기술 구조 전체 그림 → `database_schema.md`, `implementation_roadmap.md`

---

## 이 문서는
프로젝트 진행 중 **확정된 의사결정**과 그 **근거**를 시간순으로 기록합니다.
번복되지 않는 이상 결정은 여기 남아 있으며, 번복되면 **번복 기록을 새 항목으로** 추가합니다 (삭제하지 않음).

### 항목 형식

```
## YYYY-MM-DD

### [카테고리] 결정 제목

**결정:** 무엇을 확정했는가.

**근거:**
- 왜 이렇게 결정했는가 (1~4개)

**영향 범위:** (선택)
- 어떤 파일/기능이 영향을 받는가
```

### 카테고리

| 카테고리 | 의미 |
|---------|------|
| `[DATA]` | 데이터 스키마, 청크 구조, 데이터 소스 |
| `[PROCESS]` | 협업 프로세스, 핸드오프, 검수 기준 |
| `[STACK]` | 기술 스택 선택 |
| `[ARCH]` | 아키텍처, 시스템 구조 |
| `[DB]` | DB 스키마, 테이블 설계 |
| `[FLOW]` | 사용자 플로우, 서비스 흐름 |
| `[API]` | API 설계, 엔드포인트 |

---

## 2026-04-10

### [DATA] BORDER 플래그 범위 확정

**결정:** `と`, `から`, `なくちゃ`에 BORDER 플래그를 추가한다.

**근거:**
- `から`와 `ので`의 문체 차이는 N4 범위에 가깝다.
- N5에서는 초급 학습자에게 필요한 기본 의미만 우선 설명한다.
- BORDER 항목은 N5 기본 용법만 기술, 심화는 비교 청크에서 처리.

**영향 범위:**
- `grammar_chunks.border_flag` 컬럼 (N5 23개 항목 대상)
- 츠쿠야 검수 체크리스트의 BORDER 확인 항목

---

### [PROCESS] 검수 3단 레이어 구조

**결정:** 데이터 검수는 3단 레이어로 구성한다.
- L1: 오픈데이터 목록 참고 (사실 정보만)
- L2: LLM 필드 생성 (콘텐츠 자체)
- L3: 에이전트(츠쿠야) 체크리스트 검수 (품질 검증)

**근거:**
- LLM 단독 검수 시 동일 모델 편향 리스크 존재 (생성과 검증을 같은 모델이 하면 같은 실수를 놓칠 수 있음).
- 오픈데이터는 사실 정보(목록/레벨)만 제공하여 저작권 리스크를 차단.
- 체크리스트 기반 검수로 품질 일관성 확보.
- 면접 답변용으로도 "데이터 품질 관리 체계"를 명확히 설명 가능 (포트폴리오 강점).

**영향 범위:**
- `data_pipeline.md` 1, 5장 (단일 진실 원천)
- `prompts/de_sujin_prompt.md` (생성 담당)
- `prompts/jp_tsukuya_prompt.md` (검수 담당)
- 데이터 확보 워크플로우 전체 (`data_pipeline.md` 3장)

---

### [PROCESS] 생성과 검수 역할 분리

**결정:** LLM 생성은 수진이 담당하고, 검수는 츠쿠야가 담당한다. 한 에이전트가 동시에 수행하지 않는다.

**근거:**
- 생성자가 자신의 산출물을 직접 검수하면 독립성이 떨어진다.
- 별도 검수 체계가 있어야 데이터 품질을 신뢰할 수 있다.
- PM 민석의 명시적 승인이 있을 경우에만 예외 허용.

**영향 범위:**
- 수진/츠쿠야 에이전트 프롬프트
- 핸드오프 워크플로우

---

### [DATA] 이중 용법 문법 포맷

**결정:** 하나의 문법 포인트에 여러 용법이 있으면 `【용법명】` 구조로 분리 기술한다.

**근거:**
- 학습자 혼란을 줄일 수 있다.
- N5 데이터셋 전체의 설명 형식을 통일할 수 있다.
- 츠쿠야 검수 기준으로 재사용 가능.

**영향 범위:**
- `grammar_chunks.content.connection` 필드 작성 표준
- 수진 LLM 생성 프롬프트 템플릿

---

### [DATA] `だ`와 `です` 분리 기술

**결정:** 접속 규칙에서 `だ`와 `です`를 분리해서 기술한다.

**근거:**
- 둘을 섞어 쓰면 특히 `い형용사` 접속에서 혼란이 생긴다.
- 학습자 혼란 방지가 일관성보다 중요.

**영향 범위:**
- `grammar_chunks.content.connection` 필드

---

## 2026-04-14

### [STACK] Phase 1 기술 스택 확정

**결정:** `FastAPI + PostgreSQL 16 + pgvector + Redis + LangGraph + GPT-4o-mini` 조합으로 통일한다.

**근거:**
- `pgvector`를 쓰면 관계형 데이터와 벡터 검색을 한 데이터베이스에서 다룰 수 있다.
- 현재 데이터 규모(~400개 청크)에서는 PostgreSQL 기반 벡터 검색으로 충분하다.
- DataGrip 등에서 가시성이 좋다.
- `GPT-4o-mini`는 MVP 비용 통제에 유리하다.
- `LangGraph`는 상태 관리와 분기 흐름을 표현하기 적합하다.

**영향 범위:**
- `docker-compose.yml`은 `pgvector/pgvector:pg16` 이미지를 사용한다.
- `pyproject.toml`과 `poetry.lock`은 `pgvector` 기준으로 유지한다.
- 모든 문서는 벡터 검색 백엔드를 `pgvector`로 본다.

---

### [ARCH] 벡터 검색 저장소 경계

**결정:** Phase 1에서는 PostgreSQL을 관계형 저장소이자 벡터 검색 저장소로 함께 사용한다. 별도의 ChromaDB / Pinecone은 도입하지 않는다.

**근거:**
- 별도 로컬 벡터 DB를 두지 않아도 된다.
- 로컬 운영과 초기 디버깅이 단순해진다.
- 동기화 이슈 원천 제거 (단일 트랜잭션 내 임베딩 업데이트).
- 추후 Pinecone 같은 외부 서비스로 옮길 때는 `services/retrieval.py` 추상화 레이어에서만 변경.

**영향 범위:**
- `grammar_chunks.embedding VECTOR(1536)` 컬럼
- `src/services/retrieval.py` 인터페이스

---

### [DB] `grammar_chunks` 테이블 추가

**결정:** Retrieval용 원본 데이터를 저장하는 `grammar_chunks` 테이블을 별도로 둔다.

**근거:**
- 청크 메타데이터를 PostgreSQL에서 직접 조회할 수 있다.
- 원본 데이터와 벡터 인덱스를 같은 저장소에서 다루기 쉽다.
- 디버깅과 운영 확인이 수월해진다.

**영향 범위:**
- `database_schema.md` 13장

---

## 2026-04-19

### [FLOW] 익명 진단 + 로그인 이후 학습 분리

**결정:** 익명 사용자는 레벨 평가(진단)까지만 진행하고, 학습은 로그인 이후부터만 시작한다.

**근거:**
- 듀오링고 패턴: 가입 전에 서비스 가치를 체험시켜야 전환율이 올라간다 (P1: 뭐부터 해야 할지 모르겠다에 대한 체험).
- 익명 상태와 회원 상태가 혼재된 스키마는 제약 표현이 복잡하고 쿼리가 지저분해진다.
- 테이블을 익명 구간(`anonymous_sessions`, `diagnostic_*`) / 회원 구간(`users`, `learning_*`, `weak_points`, `last_session`)으로 분리하면 설계가 단순해진다.
- 학습은 복습/이어하기/약점 누적이 얽혀 있어 `user_id` 기준으로 일원화하는 것이 추적에 유리.

**영향 범위:**
- `service_flows.md` 1~3장
- `database_schema.md` 3~4장 (구간 분리 + 승계 트랜잭션)
- `api_endpoints.md` 5-2 (`POST /api/v1/auth/link-session`)

---

### [FLOW] 진단 10문항 구성 확정

**결정:** 진단 테스트는 총 10문항, 레벨 분포는 N5×4 / N4×3 / N3×3으로 고정한다.

**근거:**
- 초심자 이탈을 막으면서도 N5~N3 범위를 커버할 최소 개수.
- N5 비중을 높여 노베이스 사용자의 첫 문항 난이도 체감을 낮춘다 (첫 문제부터 어렵다고 느끼면 이탈).
- 4지선다 객관식으로 고정하여 채점 복잡도를 낮춘다.

**영향 범위:**
- `service_flows.md` 1장
- 진단 문제 seed 데이터 구성 기준

---

### [FLOW] `weak_points` 생성 시점

**결정:** 익명 진단 단계에서는 `weak_points`를 쓰지 않고, 로그인/가입 트랜잭션 시점에 한 번만 생성한다.

**근거:**
- 익명 상태에서 만들면 나중에 회원 상태로 승격할 때 중복 생성 리스크.
- 로그인 시점에 한 번만 만드는 것이 안전하고 트랜잭션으로 묶기 쉽다.
- `weak_points`에 `anonymous_session_id` 컬럼을 두지 않아도 되어 스키마가 단순해진다.

**영향 범위:**
- `api_endpoints.md` 6-4 (complete는 weak_points 쓰지 않음)
- `api_endpoints.md` 5-2 (link-session이 weak_points 일괄 생성)
- `database_schema.md` 4-4장 (링크 트랜잭션 의사코드)

---

### [FLOW] 오답 3회 강제 종료 정책

**결정:** 이해도 확인 문제에서 같은 학습 포인트에 대해 `explanation_version >= 3`이고 오답이면 학습 세션을 강제 종료하고 다음 추천을 제시한다.

**근거:**
- 같은 포인트에 무한히 갇히는 것을 방지.
- 다른 각도로 재설명 → 재출제 루프를 최대 2회까지만 허용.
- 3회 모두 오답이면 일단 우회 후 복습 스케줄로 돌려 학습 피로를 낮춘다.

**영향 범위:**
- `api_endpoints.md` 8-5 (`next_action = 'end'`)
- `service_flows.md` 2장

---

### [DB] 청크 JSON 구조를 `content JSONB`로 통합

**결정:** `grammar_chunks`의 청크 본문은 `content JSONB` 단일 필드로 통합하고, 검색 최적화 컬럼(`embedding_text`, `embedding`, `border_flag`, `level`, `chunk_type` 등)만 top-level로 둔다.

**근거:**
- 청크 타입(grammar vs compare)별로 필드 구조가 다르다.
- 스키마 변경 없이 필드 추가 가능 (마이그레이션 부담 감소).
- 필터링/인덱스가 필요한 컬럼만 top-level이면 쿼리 성능과 유연성 양립.

**영향 범위:**
- `database_schema.md` 13장, 15장

---

### [DB] `chunk_serial` 별도 컬럼 유지

**결정:** `grammar_chunks`의 PK는 UUID이지만, 사람이 읽을 수 있는 시리얼(`N5_grammar_001`)은 `chunk_serial VARCHAR(50) UNIQUE`로 별도 보존한다.

**근거:**
- UUID는 시스템 참조용으로 안전하지만 디버깅/관리 때 가독성이 떨어진다.
- 기존 수진 데이터셋이 `N5_grammar_001` 형식으로 작성되어 있어 호환성이 필요하다.
- 이중 키 운영으로 내부 안전성 + 외부 가독성 모두 확보.

**영향 범위:**
- `database_schema.md` 13장

---

## 2026-04-28

### [DATA] `grammar_point_id` 포맷 확정

**결정:** `grammar_point_id`는 `grammar_{level}_{seq:03d}` 형식으로 한다 (예: `grammar_n5_001`, `grammar_n4_001`, `grammar_n3_001`).

**근거:**
- 차후 청해(`listening`)·독해(`reading`) 등 다른 청크 타입 확장 시 일관된 prefix 사용 가능 (예: `listening_n3_001`).
- 의미가 자명하여 디버깅 가독성 우위.

**영향 범위:**
- `grammar_chunks`, `diagnostic_answers`, `learning_sessions`, `learning_records`, `weak_points`, `last_session` (6개 테이블).
- `database_schema.md` §미결 항목 정리.

---

### [DATA] 비교 청크 `grammar_point_id` 규칙

**결정:** 비교 청크의 `grammar_point_id`는 `compare_{level}_{문법1}_{문법2}` 형식으로 한다 (예: `compare_n5_ha_ga`).

**근거:**
- 약점 추적 시 비교 청크인지 ID만 보고 즉시 분간 가능.
- 두 문법 키가 ID에 모두 포함되어 RAG 보조 필터링·디버깅 자연스러움.
- 운영 중 문제 발견 시 변경 가능 (잠정 결정 — 정빈님 명시).

**영향 범위:**
- `grammar_chunks` (chunk_type='compare').
- 약점 추적·연관 청크 추천 로직.

---

### [API] `diagnosed_level` 계산 규칙

**결정:** 진단 10문항 점수와 레벨 판정 매핑은 다음과 같이 한다.
- 0~3점 → N5
- 4~6점 → N4
- 7~10점 → N3

**근거:**
- 단순 점수 구간으로 의사결정 근거를 면접에서 단순하게 설명 가능.
- Phase 2에서 LLM 보조 채점·문항 가중치 도입 시 자연스럽게 고도화 가능.

**영향 범위:**
- `POST /api/v1/diagnosis/sessions/{id}/complete`.
- `diagnostic_sessions.diagnosed_level`.

---

### [DB] 진단 문제 seed 저장소

**결정:** 진단 문제 seed 데이터는 PostgreSQL 별도 테이블(예: `diagnostic_questions`)로 저장한다.

**근거:**
- 차후 활용·수정 편의를 위한 정빈님 판단.
- FK로 `diagnostic_answers.question_id` 무결성 보장 가능.
- Phase 2 LLM 보조 문제 생성 도입 시 동일 테이블 확장 가능.

**영향 범위:**
- 신규 테이블 추가.
- Alembic Migration 1 또는 2에 포함.
- `diagnostic_answers.question_id` FK 제약.

---

### [DATA] N4/N3 청크 폴백 정책

**결정:** Phase 1 진단에 사용된 N4/N3 문항이 다루는 문법 포인트만 최소 청크를 우선 생성한다. Phase 1 기본 흐름 완성 직후 N3/N4 풀세트 확장 작업으로 이어간다.

**근거:**
- 진단(N5×4 + N4×3 + N3×3)에서 잡힌 N4/N3 약점에 대해 RAG가 빈손으로 돌아오는 UX 차단.
- Phase 1 시연·사용은 정빈님 본인 단독 → 일정 부담 적음.
- 최소 청크는 N5 검수 기준의 경량화 버전 적용 (츠쿠야 사전 합의 필요).

**영향 범위:**
- `data/curated/n4_grammar_chunks.json`, `data/curated/n3_grammar_chunks.json` (최소 ~6개).
- `weak_points` retrieval 폴백 로직 (재현).
- 검수 체크리스트 N4/N3 경량 버전 (츠쿠야).

---

### [ARCH] 캐시 L1/L2 레이어 분리

**결정:** LLM 응답 캐시는 Redis(L1) + PostgreSQL `llm_response_cache`(L2) 이중 레이어로 운영한다.
- 조회 순서: Redis → PostgreSQL → LLM 호출 → 양쪽 저장.
- L1 (Redis): 24h TTL, 인메모리 고속 캐시, 휘발.
- L2 (PostgreSQL): 영구 저장, token_usage 통계 추적.

**근거:**
- Redis 단독 시 서버 재시작 후 캐시 손실 → LLM 비용 재발생.
- PostgreSQL 단독 시 인메모리 고속 응답 불가.
- 두 레이어 모두 docker-compose에 이미 존재 → 추가 인프라 비용 없음.

**영향 범위:**
- `src/services/cache_service.py` (신규).
- LangGraph 캐시 노드 로직.
- `llm_response_cache.cache_key` 포맷에 cache_type prefix 추가 (REC-09).

---

### [API] URL path parameter 케이스 통일

**결정:** API URL의 path parameter는 `snake_case`로 통일한다 (예: `{diagnosis_session_id}`).

**근거:**
- FastAPI 표준 (Python 변수명을 path parameter로 그대로 사용).
- camelCase 유지 시 `Path(alias=...)` 처리 필요 + OpenAPI docs와 코드 불일치 위험.

**영향 범위:**
- `api_endpoints.md` 전체 URL 표기 수정.
- 모든 API 라우트 핸들러 함수 시그니처.

---

## 2026-04-29

### [PROCESS] N5 마스터 리스트 출처 인용 방식

**결정:** N5 84개 문법 포인트 마스터 리스트는 3~5개 권위 출처의 교차 검증 + 빈도 합집합/교집합으로 산정한다.

**근거:**
- 단일 권위 출처 의존 시 누락 위험. 단일 출처 분류를 그대로 따르면 저작권 측면에서도 약점.
- "왜 이 84개?"의 근거가 면접 답변에서 강력함.
- 사실 정보 기반 접근(공통 빈출 항목)이라 저작권상 안전.

**영향 범위:**
- `docs/planning/session_2/de_sujin/01_n5_master_list.md`.
- 마스터 리스트 표에 출처 풀 ID 컬럼 포함.

---

### [PROCESS] 외부 네트워크 호출(WebFetch 등) 정책

**결정:** Phase 1 기획·작성 단계의 외부 네트워크 호출(WebFetch / curl / wget)은 **차단 유지**한다. 부족한 부분이 발견되면 사안별 정빈님 명시 승인 후 일회성 사용.

**근거:**
- AGENTs.md 기존 정책(외부 네트워크 호출 = 사람의 명시적 결정 필요)을 그대로 채택.
- 모델 도메인 지식 + 내부 문서 + 교차 검증 방식으로 1차 수집 가능.

**영향 범위:**
- 모든 에이전트(수진/재현/츠쿠야/PM) 작업.
- 부족 시 차후 별도 결정으로 일회성 승인 가능.

---

### [DATA] JLPT 출제기준 / 기출 문제 사용 정책

**결정:**
- 구판(1989) 출제기준은 후순위로만 참고하고, 최신 자료(공식 가이드·시판 교과서·공개 학습 자료)를 출처 풀 우선순위로 한다.
- 기출 문제는 직접 사용·인용 금지. **사실 정보 추출 참고만 허용** (예: "어떤 문법이 N5에 등장하는가"의 빈도 정보).

**근거:**
- 구판은 시간 차이로 현재 출제 추세와 괴리 가능.
- 기출 문제 직접 사용은 저작권·라이선스 측면에서 위험.
- 사실 정보 자체는 저작권 보호 대상이 아님(facts).

**영향 범위:**
- 수진 출처 풀 정의.
- 츠쿠야 검수 시 출처 인용 검증 항목.

---

### [DATA] N5 카테고리 L1 입자도

**결정:** N5 문법 카테고리 L1은 8 그룹으로 한다.

L1 8 그룹: 조사 / 활용 / 문형·표현 / 종조사 / 지시·연체 / 의문 표현 / 시간·수량 표현 / 접속·연결.

세부 조사가 필요한 그룹은 차후 별도 추가 조사 가능(정빈님 명시).

**2026-04-30 갱신:** Decision B(부사류 14개 N5 청크 추가)에 의해 부사류 L1-9 신설 → L1 **9 그룹**으로 변경. 9번째 그룹: 부사류. (츠쿠야 01 마스터 리스트 검수 ISSUE-03 반영)

**근거:**
- 84개 / 8 = 평균 10.5개/그룹 — 분류 입자도 적당.
- 12 세분화는 그룹별 항목 수 부족으로 RAG 검색 시 차별화 약화.

**영향 범위:**
- `02_n5_category_taxonomy.md` (수진 산출물).
- 차후 N4/N3 taxonomy 확장 시 동일 입자도 적용.

---

### [PROCESS] Stage 0 제안서 분할 단위

**결정:** Stage 0 골격 제안서는 docker / FastAPI / Alembic 별 3분할로 작성하고, L3 운영 디테일은 별도 분할로 추가한다 (총 4 md).

**근거:**
- docker가 base이고 FastAPI/Alembic이 DSN·Redis URL을 따라오는 구조 → 트랙별 순차 확정 자연스러움.
- 정빈님 빈번 소통 모드와 매칭 (트랙별 즉시 피드백 가능).

**영향 범위:**
- 재현 산출물 4 md.
- 다음 세션 Stage 0 구현 시 트랙별 작업 분할.

---

### [PROCESS] Stage 0 제안서 detail level 정책

**결정:** Stage 0 제안서는 L2(실행 가능 minimal 코드) 수준으로 작성하고, L3 운영 디테일은 별도 문서 `04_l3_operational_issues.md`로 분리한다.

**근거:**
- 다음 세션 구현 트랙에서 제안서 코드를 그대로 옮기면 동작 → 정빈님 시간 절약.
- L3 운영 항목(Redis password / PG tuning / non-root / multi-stage build / `.env` 보안 등)은 MVP 이후 보강 — 별도 추적으로 분실 리스크 제거.

**영향 범위:**
- `01_docker_setup_proposal.md`, `02_fastapi_entry_proposal.md`, `03_alembic_init_proposal.md` (L2).
- `04_l3_operational_issues.md` (신규, L3 issue list).

---

### [DB] Alembic baseline 정책

**결정:** Alembic baseline은 빈 `0001_initial.py`(no-op revision)로 시작하고, Stage 1부터 도메인 스키마 마이그레이션을 분리해 쌓는다. 단 Stage 1 진입 시 즉시 채워질 MVP DB 설계 항목(테이블 이름·책임)을 baseline 제안서에 명시한다.

**근거:**
- 표준 alembic 패턴 — history 가독성·향후 reset/squash anchor 역할.
- baseline에 도메인 테이블이 들어가면 향후 reset 시 어색.

**영향 범위:**
- `migrations/versions/0001_initial.py` (빈 revision, 다음 세션 구현).
- Stage 1 마이그레이션 0002+ 에 실제 스키마.
- `03_alembic_init_proposal.md`에 MVP DB 설계 항목(`users`, `anonymous_sessions`, `diagnostic_questions`, `grammar_chunks`, `comparison_chunks`, `learning_records`, `llm_response_cache` 등) 표시.

---

### [ARCH] docker-compose 미사용 — 개별 docker run

**결정:** Phase 1 인프라는 `docker-compose`를 사용하지 않는다. PostgreSQL(pgvector)·Redis는 개별 `docker run`으로 띄우고, 앱은 `Dockerfile`로 이미지 빌드하되 dev 단계는 호스트에서 `poetry run uvicorn` 실행 옵션을 함께 제공한다. compose 도입은 Phase 2 이후 서버 규모 확대 시 재검토.

**근거:**
- 1인 개발·소규모 서버 단계에서 compose 운영 부담이 ROI에 비해 큼 (정빈님 명시: "컴포즈 운영할 정도로 지금 서버가 크지 않음").
- 개별 `docker run` + 호스트 실행은 dev iteration 속도가 빠름.
- 시작 순서·healthcheck는 Makefile/스크립트 또는 수동 명령으로 처리 가능.

**영향 범위:**
- `01_docker_setup_proposal.md`(compose 형식 X, 개별 `docker run` + `Dockerfile` + 운영 가이드).
- 다음 세션 Stage 0 구현에서 `docker-compose.yml` 작성 X.
- `decision_log.md` 2026-04-14 [STACK] 결정의 docker-compose 언급은 "개념상 컴포넌트 명세" 한정으로 재해석.
- `CLAUDE.md` Infra 항목(현재 "Docker Compose")은 본 결정 반영해 추후 갱신 필요.

---

### [STACK] Python 버전 확정

**결정:** Python 3.12 사용.

**근거:**
- `asyncpg` / `pgvector-python` 양쪽 안정성.
- 3.13은 일부 의존성(특히 비동기·DB 드라이버) 호환성 검증 부담.
- 3.11은 신규 기능(`except*`, `Self` typing 등) 활용 차원에서 약간 후퇴.

**영향 범위:**
- `Dockerfile` base image (`python:3.12-slim`).
- `pyproject.toml` `python = "^3.12"`.

---

### [STACK] Stage 0 의존성 일괄 승인

**결정:** 다음 세션 Stage 0 구현 진입을 위해 아래 8개 패키지 일괄 추가 승인.

| 패키지 | 버전 | 용도 |
|---|---|---|
| `fastapi` | `^0.115` | 웹 프레임워크 |
| `uvicorn[standard]` | `^0.30` | ASGI 서버 + uvloop |
| `pydantic` | `^2.7` | 모델 검증 |
| `pydantic-settings` | `^2.3` | `.env` 로드 + Settings 클래스 |
| `sqlalchemy[asyncio]` | `^2.0` | ORM (async) |
| `asyncpg` | `^0.29` | PostgreSQL async 드라이버 |
| `redis[hiredis]` | `^5.0` | Redis async 클라이언트 + C 가속 |
| `alembic` | (latest) | DB 마이그레이션 |

**근거:**
- Stage 0 구현 트랙 진입 차단 항목.
- 세션 2 02·03 제안서 §패키지 의존성에서 도출된 최소 세트.

**영향 범위:**
- `pyproject.toml` 다음 세션 `poetry add` 일괄 실행.
- 다음 세션 Stage 0 구현 시작 시점.

---

### [PROCESS] L3 운영 디테일 정빈님 결정 (Stage 0~1 한정)

**결정:** 04 L3 issue list 8 항목에 대해 정빈님이 다음과 같이 판단.

| L3 | 정빈님 결정 |
|---|---|
| L3-01 Redis password | dev 미적용. prod는 별도 운영 (Phase 2 이후 분리) |
| L3-02 PG 파라미터 튜닝 | 필요 시 진행 (재현 판단) |
| L3-03 non-root 컨테이너 user | **미채택** — root 권한으로 운영 |
| L3-04 multi-stage Dockerfile | 04 권고대로 (Stage 1 진입 시 도입 검토) |
| L3-05 `.env` 보안 | **이미 처리됨** (`.gitignore` 등록 확인 완료, 2026-04-29 lead 점검) |
| L3-06 로그 수집 | 차후 (Stage 2) |
| L3-07 PG 백업 | 데이터 적재 전 처리 (Stage 1) |
| L3-08 모니터링 | Phase 2~3 진입 시 별도 결정 |

**근거:**
- 1인 개발·소규모 서버 단계의 ROI 판단 (정빈님 명시).
- L3-03 non-root는 정빈님 운영 환경상 컨테이너 user 분리 효익이 작다는 판단.

**영향 범위:**
- `04_l3_operational_issues.md` 각 카드에 정빈님 결정 메모 추가.
- 다음 세션 Stage 0 구현 시 L3-01 / L3-03 / L3-05는 즉시 적용 사항으로 진입.

---

### [PROCESS] 다음 세션(session_3) 트랙 우선순위

**결정:** 다음 세션은 다음 3 트랙으로 진행.

| 우선순위 | 트랙 | 주축 |
|---|---|---|
| 1 | MVP 11 테이블 재검토 워크숍 (데이터 형식 + API ↔ DB 스키마 매핑) | 정빈님 + 재현 |
| 2 | N5 전체 츠쿠야 검수 (마스터 리스트 + taxonomy + BORDER 5건 + 비교쌍 후보) | 수진 + 츠쿠야 |
| 3 (병렬) | Stage 0 구현 (테이블 워크숍 의존 X 부분 — Docker / FastAPI 엔트리 / Alembic baseline) | 재현 |

**근거:**
- 정빈님 명시: "테이블은 데이터 들어오는 형식이랑 API 고려해서 다시 검토"·"수진+츠쿠야 전체 검토".
- 트랙 1이 트랙 3의 일부 의존성(스키마 변경 가능성)을 가지므로 우선순위 1.
- 트랙 2는 트랙 1·3과 도메인 겹침 없어 동시 진행 가능.

**영향 범위:**
- 다음 세션 spawn 대상: `be_jaehyeon`, `de_sujin`, `jp_tsukuya` (츠쿠야 신규 합류).
- 세션 2 핸드오프 (`session_2/pm_minseok/summary.md` §"다음 세션 우선 작업").

---

## 2026-04-30 — 세션 2 추가 작업 (xlsx 교차검증)

> 추가 작업 트리거: 정빈님 4월 10일 작업본 `N5_전체목록_기준표_v2.xlsx`(84 항목)을 세션 2에 추가 투입. 수진 03 보고서를 통해 차이점 매핑 + 결정 도출.

---

### [DATA] (사후 등록) 청크 타입 — text 단일 (vector 분리 X)

**결정:** N5 청크는 `chunk_type = 'point' | 'compare'` 단일 테이블(`grammar_chunks`)에 통합. vector 컬럼은 같은 테이블에 컬럼으로 보유.

**근거:**
- 별도 vector 청크 테이블 신설 시 JOIN 비용 + 운영 복잡도 증가.
- 03 보고서 §6 누락 #2 — 원 결정 시점 4월 10일경, 본 로그에 사후 정식 등록.

**영향 범위:**
- `database_schema.md` `grammar_chunks` 단일 테이블 정의 적용.
- 재현 03 제안서 통합 테이블 설계 정합.

---

### [DATA] (사후 등록) MVP 범위 — N5~N3 진단 + 학습 기록만

**결정:** Phase 1 MVP는 N5~N3 진단 흐름과 학습 기록 저장까지로 범위를 한정. 음성 입력·교사 추천·문제 자동 생성 등 부가 기능은 Phase 2 이후.

**근거:**
- 1인 개발자 자원 제약 + 핵심 가치 검증 우선.
- 03 보고서 §6 누락 #3 사후 등록.

**영향 범위:**
- 다음 세션 트랙 우선순위와 정합.
- `implementation_roadmap.md` Phase 1 범위 그대로.

---

### [PROCESS] (사후 등록) 작업 순서 — 데이터 → 청크 → API → UI

**결정:** Phase 1 작업 순서는 (1) 데이터 적재 → (2) 청크 생성 + 임베딩 → (3) API 엔드포인트 → (4) UI/클라이언트.

**근거:**
- 데이터 정합성 확보 후 상위 레이어 진입이 재작업 비용 최소화.
- 03 보고서 §6 누락 #5 사후 등록.

---

### [DATA] (사후 등록) 비교쌍 3-way → 2-way 단순화

**결정:** 3개 항목 동시 비교쌍은 N5 단계에서 모두 2-way 쌍으로 분해.

**근거:**
- N5 학습자 인지 부담 + 청크 임베딩 일관성.
- 03 보고서 §6 누락 #9 사후 등록.

---

### [DATA] (사후 등록) とても vs すごく 비교쌍 등록

**결정:** とても / すごく 비교쌍은 N5 비교쌍 풀에 등록 (격식 차이 학습용).

**근거:**
- 학습자 빈출 혼동 항목.
- 03 보고서 §6 누락 #10 사후 등록.

---

### [DATA] BORDER 7개 추가 등록 + N5/N4 동시 노출 정책

**결정:** xlsx v2 BORDER 23개 중 수진 01 매핑불가 7개(だろう / んです / のです / ので / てある / てから / つもり)를 모두 **N5 추가 BORDER**로 등록. N5 학습 단계에서도 노출하고, N4에서 정식 학습 시 다시 강조.

**근거:**
- 정빈님 명시: "N5에 포함되기는 어려운데 N4 같지는 않은 것이 BORDER. 추가하고 N5와 N4에서 같이 다루며 차후 강조."
- 시험 빈출도와 학습자 단계 사이 갭 처리 정책.

**영향 범위:**
- `01_n5_master_list.md` BORDER 7개 추가 (총 N5 BORDER 30 내외 예상).
- 02 taxonomy `border_n4_flag` 정책 명시.

---

### [DATA] 항목 정책 — Q-A YES (부사류 N5 포함) / Q-B 이형태 분리

**결정:** xlsx v2 84 항목 vs 수진 01 64 항목 차이의 근본 정책.
- **Q-A: 부사류 14개를 N5 문법 청크로 포함** (jlptsensei 채택 항목 그대로).
- **Q-B: 이형태(だろう/でしょう, んです/のです 등)는 분리 항목으로 유지** (통합 X).

**근거:**
- 정빈님 명시: "시험 위주이니 jlptsensei 철학을 따르는 게 맞다."
- 시험 패턴 중심 진단 정확도 우선.

**영향 범위:**
- `01_n5_master_list.md` 항목 수 ~84로 재정렬 (수진 추가 항목 + 부사류 + 이형태 분리).
- 02 taxonomy 부사류 카테고리 명시.

---

### [PROCESS] 부사류 추가 시 lead 에스컬레이션

**결정:** Q-A 부사류 N5 포함 정책 후, 차후 새로운 부사류 항목이 발견될 경우 **수진 자율 추가 금지 / lead 에스컬레이션 후 결정**.

**근거:**
- 부사 vs 문법 청크 경계 모호성 — 정책 일관성 유지를 위해 단일 게이트.
- 정빈님 명시: "차후 부사류 추가 시 에스컬레이션."

---

### [DATA] 비교쌍 24쌍 모두 포함 + 츠쿠야 검토에서 확정

**결정:** xlsx v2 비교쌍 21쌍 + 수진 추가 3쌍 = 24쌍 모두 N5 비교쌍 풀로 진입. 최종 확정은 츠쿠야 감리 검수 후.

**근거:**
- 정빈님 명시: "다 포함해서 만들고 차후 츠쿠야 검토."
- RAG 처리 정합성은 츠쿠야 검수에서 판정.
- "자주 나올 질문" 우선순위 + RAG 외 처리는 차후 리스트업 (현재 단계 제외).

**영향 범위:**
- 수진 비교쌍 24쌍 정리본 → 츠쿠야 spawn 입력.

---

### [DATA] 출처 풀 — SRC-07 jlptsensei 정식 추가

**결정:** N5 데이터 출처 풀에 `SRC-07 jlptsensei.com`을 정식 등록. SRC-01~06과 동급으로 사용하며, 단일 출처 의존 금지 + 교차검증 도구로 활용.

**근거:**
- 정빈님 명시: "jlptsensei를 포함하여 교차 검증 및 데이터를 생산할 것. 교차검증에 필요한 요소 중 하나로 사용."
- xlsx v2의 단일 출처(시험 패턴 중심) 한계 보완.

**영향 범위:**
- `01_n5_master_list.md` 출처 컬럼 SRC-07 추가.
- 신규 항목 등록 시 SRC-01~07 중 2개 이상 교차검증 권장 (강제 X).

---

## 2026-06-05 — 츠쿠야 검수 후속 결정 7건 (E-5 ~ E-9 + Q5 + Q6)

> 츠쿠야 session_3 검수 6 산출물 (`docs/planning/session_3/jp_tsukuya/`) 결과 정빈님 일괄 응답. PM 추천 전부 채택.

### [DATA] E-5 — 비교쌍 #18 (でも/しかし/けど) 3-way 처리

**결정:** 비교쌍 #18을 **제거**한다. 총 비교쌍 수 24 → **23쌍**으로 확정.

**근거:**
- 2026-04-30 decision_log "3-way → 2-way 분해" 결정과 직접 모순.
- 옵션 ② 2-way 분해(25쌍)는 Decision C "24쌍" 명시 위배.
- 옵션 ③ 예외 유지는 decision_log 모순 잔존.
- しかし/けど는 다른 쌍(#13, #14, #17 등)에서 다뤄지므로 학습 손실 적음.

**영향 범위:**
- `02_n5_category_taxonomy.md` 비교쌍 목록에서 #18 제거.
- `06_n5_comparison_chunks_v1.md` 본문 #18 청크 제거.
- 비교쌍 총수 표기 24 → 23 일괄 갱신.

---

### [DATA] E-6 — N4 항목 참조 비교쌍 처리 (E-23 つもり vs 予定)

**결정:** N4 항목(予定)을 참조하는 비교쌍은 **별도 compare_id 등록 없이 보류**한다. 대신 N5 측 청크(つもり) 본문에 N4 표현 메타 설명 추가.

**근거:**
- 予定는 N4, N5 청크 미존재 → RAG hit 불가.
- 별도 N4 청크 생성은 범위 확대 → Phase 1 N5~N3 진단 범위 외.
- 메타 설명만 추가하면 학습자 인지 가능.

**영향 범위:**
- `06_n5_comparison_chunks_v1.md` 쌍 #20 제거 또는 메타 처리.
- `grammar_n5_091` (つもり) point 청크 본문에 "予定는 N4, 계획성 강조" 메모 추가.

---

### [DATA] E-7 — 이형태 항목 독립 ID 부여 정책 (서픽스 방식)

**결정:** 이형태 항목은 **서픽스 방식**으로 독립 ID 부여. 패턴: `grammar_n5_{base}_{variant}`.

대상:
- `grammar_n5_026_informal` (ちゃいけない — 026 てはいけない 구어)
- `grammar_n5_082_keisiki` (けれども — 082 けど 형식체)
- `grammar_n5_035_alt` (ないといけない — 035 なければなりません 이형태)

**근거:**
- 비교 청크 작성 가능 (compare_id 명확).
- 이형태 추적성 유지.
- 마스터 리스트 총수 증가 없음 (서픽스라 base와 묶임).

**영향 범위:**
- `05_n5_l3_tag_assignment_v1.md` 이형태 항목 추가 정의.
- `06_n5_comparison_chunks_v1.md` 쌍 #14, #17, #23 compare_id 확정.

---

### [DATA] E-8 — ★ 가중치 조정 (2건)

**결정:** 다음 2 비교쌍을 ★★☆ → **★★★** 승급.
- 비교쌍 #4 だけ vs しか
- 비교쌍 #14 から vs ので

**근거:**
- だけ/しか: 한국어 학습자 최빈 혼동, jlptsensei 시험 빈출.
- から/ので: N5→N4 BORDER 핵심 비교쌍, 시험 빈출도 높음.

**영향 범위:**
- `02_n5_category_taxonomy.md` 비교쌍 가중치 갱신.

---

### [DATA] E-9 — `comparison_pair` 메타 태그 역할 정의

**결정:** L3 메타 태그 `comparison_pair`는 **"비교 청크 생성 트리거"**로 정의. taxonomy 비교쌍 목록(23쌍)이 단일 진실 공급원. taxonomy 외 추가 등록 금지.

**근거:**
- 자유 등록 시 의도하지 않은 비교 청크 RAG hit 발생.
- taxonomy ↔ L3 태그 정합성 일원화로 추적성 ↑.
- 신규 비교쌍 후보는 taxonomy 정식 등재 절차 거침.

**영향 범위:**
- `05_n5_l3_tag_assignment_v1.md` 츠쿠야 03 검수 ISSUE-05/06 (i/na 형용사 비교, 빈도 부사 3각, 013 ↔ 040 등) 모두 제거.
- 신규 비교쌍 필요 시 02 taxonomy 갱신 plan 별도 제출.

---

### [STACK] Q5 — openpyxl 의존성 추가 승인

**결정:** `openpyxl` 의존성 추가 승인. `poetry add openpyxl` 실행 완료 (v3.1.5).

**근거:**
- 정빈님 요구: 완료된 데이터 산출물 = MD + xlsx 두 형식 필수.
- stdlib zipfile + xml.etree 우회 가능하나 코드 양 ↑ / 운영 부담 ↑.
- xlsx 한정 도구 추가 1개로 운영 효율 확보.

**영향 범위:**
- `pyproject.toml`, `poetry.lock` 갱신.
- 수진 v2 산출물부터 xlsx 변환 적용.
- 부수 효과: pgvector 0.4.2도 의존성 그래프상 자동 설치됨.

---

### [DATA] Q6 — `point` 타입 embedding_text 길이 스펙

**결정:** `point` 타입 청크의 `embedding_text` 길이를 **150~270자**로 정식 채택.

**근거:**
- text-embedding-3-small 컨텍스트 8191 토큰 — 길이 부담 없음.
- `point` 타입은 RAG 검색 대상, 설명 풍부할수록 의미 유사도 매칭 정확도 ↑.
- `compare` 타입의 짧은 스펙(50~100자)은 "쌍별 특화 검색" 목적, 별도 적용.

**영향 범위:**
- 신규/갱신 청크 작성 시 `point` 길이 150~270자 가이드라인 적용.
- 츠쿠야 검수 ISSUE-05 (05_review) 해소.

---

## 2026-06-06 — 츠쿠야 사전 검수 후속 결정 4건 (E-10 ~ E-13)

> 츠쿠야 session_3 사전 검수 산출물(`07_pre_v2_check.md`) 결과 정빈님 응답. v2 plan 작성 차단 항목 정리.

### [DATA] E-10 — E-6 적용 후 비교쌍 총수 명확화

**결정:** E-6 결정 본문 "별도 compare_id 등록 없이 보류" = **해석 A 채택**. 비교쌍 #20 (つもり vs 予定)를 taxonomy에서 **제거**. 총 비교쌍 = **22쌍** (E-5 후 23 → E-6 후 22).

**근거:**
- taxonomy = 비교쌍의 단일 진실 공급원. 잔류 메타 방식은 E-9 (comparison_pair = 비교 청크 트리거) 정의와 모순.
- 予定 N4 메타 설명은 091(つもり) point 청크 본문에 통합 (E-6 본문 그대로).

**영향 범위:**
- `02_n5_category_taxonomy.md`: 클러스터 E #20 제거, 총수 23 → 22.
- `06_n5_comparison_chunks_v1.md`: #20 비교 청크 제거.
- `04_n5_chunk_samples_v1.md`: 091(つもり) point 청크 본문에 메타 설명 추가 시 반영.

---

### [DATA] E-11 — E-7 variant 항목 카운팅 (별도 시트 분리)

**결정:** 이형태 서픽스 항목(E-7)을 **별도 시트 `variant_chunks`로 분리 관리**. 마스터 리스트 카운팅에 포함하지 않음.

대상 variant (3건):
- `grammar_n5_026_informal` (ちゃいけない)
- `grammar_n5_082_keisiki` (けれども)
- `grammar_n5_035_alt` (ないといけない)

**근거:**
- E-7 본문 "서픽스라 base와 묶임 → 총수 증가 X"의 실현 방법으로 카운팅 분리.
- 데이터 구조상 별도 entity (RAG 인덱스 / L3 JSON / compare_id) 필요 → 별도 시트가 깔끔.
- base item과 variant 추적성 모두 확보 (`variant_of` 컬럼 또는 시트 분리로 명시).
- 츠쿠야 사전 검수 §3-1 권고 옵션 C 채택.

**영향 범위:**
- `n5_master.xlsx` 신규 시트 `variant_chunks` 추가 (E-13 채택 후 구조).
- 마스터 리스트 카운팅: base 109 (E-12 후, 정정) + variant 3 = 별도 표기.
- BORDER 카운팅: variant도 BORDER 후보일 수 있음 (츠쿠야 재검수 단계 평가).
- compare_id 명명 패턴: `compare_n5_{base}_{variant_id}` 형식 사용 가능.

---

### [DATA] E-12 — v2.xlsx 누락 5건 추가 (마스터 105 → 109)

> 정정 이력: 2026-06-06 — 산수 오류 발견 (105 − 1 [E-1 grammar_n5_061 제거] + 5 [E-12 신규] = 109). 본문 "110" 전부 "109"로 정정 (정빈님 ack).

**결정:** 츠쿠야 사전 검수 §2-③에서 발견한 **N5 교재·시험 빈출 핵심 5건을 모두 마스터 리스트에 추가**. 마스터 base 항목 총수 105 → **109** (E-1 적용 후 104 + 신규 5건).

추가 항목 (grammar_point_id는 v2 plan에서 부여):
| 항목 | 한국어 | 1차 출처 |
|---|---|---|
| ほうがいい | ~하는 편이 좋다 | Genki / みんなの日本語 / TRY! |
| なくてもいい | ~하지 않아도 된다 | 동상 |
| たことがある | ~한 적이 있다 (경험) | Genki L19 |
| たり〜たりする | ~하기도 하고 | Genki L11 |
| とき | ~할 때 | Genki L16 |

**근거:**
- 정빈님 명시: "중요한거면 넣어서".
- 5건 모두 SRC-02/03/04 (Genki / みんなの日本語 / TRY!) 다중 출처 명시.
- RAG 진단 시 hit 안 되면 학습자 UX 손실 (츠쿠야 평가).
- 의도적 제외 사유 없음 (수진 산출물의 자연 누락으로 판단).

**영향 범위:**
- `01_n5_master_list.md` v2: 5 항목 신규 추가 (ID·L1·L2·출처·BORDER 후보 여부 부여).
- `02_n5_category_taxonomy.md` v2: L1/L2 배정 (PM 후속 권고 — ほうがいい/なくてもいい/たことがある/たり〜たりする → 문형·표현 / とき → 시간·수량). 통계 갱신.
- `05_n5_l3_tag_assignment_v1.md` v2: 5 항목 L3 JSON 신규.
- `06_n5_comparison_chunks_v1.md` v2: 비교쌍 후보 검토 (예: なくてもいい ↔ てはいけない, たことがある ↔ ている 등 — 수진 v2 plan에서 제안).
- `04_n5_chunk_samples_v1.md` v2: 추가 청크 샘플 작성 (선택, 츠쿠야 재검수 단계).
- BORDER 후보 여부는 츠쿠야 재검수에서 평가.

---

### [PROCESS] E-13 — xlsx 파일 분리 단위 최종 확정

**결정:** v2 산출물 xlsx 분리 단위 = **2 파일 + 다중 시트** (옵션 A 채택).

#### `n5_master.xlsx` (5 시트, E-11 반영)

| 시트 | 내용 | DB 매핑 |
|---|---|---|
| `master_list` | 109 base 항목 (E-12 적용, 정정) | `grammar_chunks` (chunk_type='point') |
| `taxonomy_def` | L1 9그룹 + L2 소분류 정의 | seed 또는 enum reference |
| `l3_assignment` | 항목별 L3 태그 매트릭스 | `grammar_chunks.l3_tags JSONB` |
| `border_meta` | BORDER 상세 (이유 + N5 범위 + N4 심화) | `grammar_chunks.border_meta JSONB` |
| `variant_chunks` | E-11 variant 3건 (`_informal` / `_keisiki` / `_alt`) | `grammar_chunks` (chunk_type='variant') |

#### `n5_comparison.xlsx` (2 시트)

| 시트 | 내용 | DB 매핑 |
|---|---|---|
| `comparison_pairs` | 25쌍 (E-10 후 22 + E-16 +3) + ★ + 클러스터 | `comparison_chunks` 또는 `grammar_chunks` (chunk_type='compare') |
| `comparison_chunks` | 각 쌍 본문 + 예문 + embedding_text | 동상 |

#### 운영 데이터 위치

- 운영 진실: `data/n5/n5_master.xlsx`, `data/n5/n5_comparison.xlsx`
- 스키마 명세: `data/schema/n5_master_schema.md`, `data/schema/n5_comparison_schema.md`
- chunk_samples (04 산출물)는 본 단계 xlsx 변환 대상 X — MD 유지. 차후 105+ 청크 전체 생성 stage에서 별도 처리.

**근거:**
- DB 적재 단위 단순 (시트 ↔ 테이블 1:1 매핑).
- 운영 편의 + 확장성 (N4/N3는 `n4_master.xlsx` 동일 패턴).
- taxonomy/L3는 master와 강결합 → 동일 파일 내 시트가 자연스러움.
- comparison은 별도 도메인 (RAG 분리 단위).

**영향 범위:**
- 수진 v2 plan 작성 시 위 구조로 산출물 분리.
- DB 적재 파이프라인 (트랙 3 Stage 1 구현) = 시트 단위 SQLAlchemy 매핑.
- `data/` 디렉터리 신설 (lead 또는 재현 워크숍 단계에서).

---

### [PROCESS] E-14 — 츠쿠야 v2 재검수 changelog 형식 (옵션 A)

**결정:** v2 재검수 시 수진 변경 이력 전달 형식 = **옵션 A 채택**. 수진이 v2 plan에 **`§v2 changelog` 섹션을 필수 포함**하여 결정 11건 + E-14~E-16 → v2 적용 매핑 + 즉시 적용 10항목 + 결정 후 5항목 + variant 분리 + 비교쌍 25쌍 (E-16 +3 후) 변경 이력을 모두 명시. 츠쿠야는 changelog 기반 변경 영역만 정밀 검수 (전수 재검수 X).

**근거:**
- 츠쿠야 명확화 질문 (세션 3 사전 검수 후속): "v2 재검수 시 수진의 변경 이력(changelog/diff)을 함께 받는가, 아니면 츠쿠야가 `07_pre_v2_check.md` 기준 스냅샷으로 직접 대조하는가?"
- 옵션 A 트레이드오프: 수진 작업 부담 미미 (결정 11건 + v2 적용 15항목 이미 트래킹됨) vs 츠쿠야 누락 리스크 ↓ + 향후 v3·v4 표준 형식 정착.
- 데이터 거버넌스 표준화: 단순 일회성 운영 결정이 아니라 향후 N4/N3 v2·v3 단계에도 동일 적용 권고.

**영향 범위:**
- 수진 v2 plan (`docs/planning/session_4/de_sujin/`): `§v2 changelog` 섹션 필수.
- 츠쿠야 재검수 산출물 (`docs/planning/session_4/jp_tsukuya/`): changelog 기반 변경 영역 정밀 검수 + variant 3건 BORDER 별도 평가 (E-15 참조).
- 향후 N4/N3 단계: 동일 형식 적용 권고.

---

### [PROCESS] E-15 — variant 3건 BORDER 재평가 산출물 형식 (옵션 a 통합)

**결정:** variant 3건 (ちゃいけない / けれども / ないといけない) BORDER 사유 재평가 결과를 **v2 재검수 산출물 안에서 별도 절(節)로 명확히 구분하여 통합 제출** (옵션 (a) 채택). 별도 산출물 분리 X.

**근거:**
- E-11 채택으로 variant_chunks가 v2의 새로운 시트가 되므로, BORDER 재평가는 v2 재검수의 자연 대상에 포함됨.
- 산출물 분리(옵션 b) 시 정빈님 검토 부담 ↑ + 세션 90분 한도 압박.
- 별도 절(節) 구분으로 모듈성 확보 → 통합과 분리의 장점 모두 확보.
- 츠쿠야 default 선호 = (a) 통합.

**영향 범위:**
- 츠쿠야 v2 재검수 산출물: `§variant BORDER 평가` 절 또는 동등 표제로 명확 구분.
- BORDER 카운팅: variant 3건의 BORDER 후보 여부가 정해지면 그 결과를 별도 카운팅하여 base 21 + variant N 형식으로 표기 (구체 형식은 츠쿠야 재검수 산출물에서).

---

### [DATA] E-16 — E-12 신규 5건 비교쌍 후보 3쌍 taxonomy 등재 (22쌍 → 25쌍)

**결정:** 수진 v2 plan §6-3에서 제안한 E-12 신규 5건 관련 비교쌍 후보 3쌍을 **모두 taxonomy에 등재** (v2 단계에서 처리, 후속 미루지 않음). 비교쌍 총수 22 → **25쌍**.

등재 대상:
| 후보 쌍 | 좌 | 우 | 혼동 포인트 |
|---|---|---|---|
| なくてもいい vs てはいけない | 107 | 026 | 허가 vs 금지 (한국어 학습자 최빈) |
| たことがある vs ている | 108 | 023 | 경험 과거 vs 현재진행/상태 (시제 혼동) |
| ほうがいい vs たほうがいい | 106 | — (자기 비교) | 현재형 vs 과거형 권유 뉘앙스 |

**근거:**
- 정빈님 명시: "비교쌍까지 하고 그냥 가자. 그래야 뭐 할 때 덜 불편할 거 아냐" — 후속 단계로 미루면 v3 또는 N4 진입 시 재진입 비용.
- 3쌍 모두 한국어 학습자 최빈 혼동 패턴 (수진 §6-3 제안).
- E-9 원칙 (taxonomy = 비교쌍 단일 진실 공급원) 준수.
- 츠쿠야 재검수 부담 ↑이나, v2 안정화 한 번에 묶는 게 운영 효율.

**영향 범위:**
- `03_n5_category_taxonomy_v2.md`: 비교쌍 22쌍 → 25쌍. 클러스터 배정은 수진 작성 시 결정 (PM 권고: 허가/금지 = 클러스터 B 또는 신규, 시제 = 신규, 권유 뉘앙스 = 신규).
- `06_n5_comparison_chunks_v2.md`: 신규 3쌍 본문 작성 (compare_id `compare_n5_107_026` / `compare_n5_108_023` / `compare_n5_106_self`).
- `04_n5_l3_tag_assignment_v2.md`: 해당 base 항목 comparison_pair JSON에 신규 compare_id 추가.
- 츠쿠야 재검수: 3쌍 신규 본문 정합성 + native 표현 검수 포함.

**ほうがいい 자기 비교 처리 메모:** "ほうがいい (~하는 편이 좋다, 현재형)" vs "たほうがいい (~하는 편이 좋았다 → ~한 편이 좋다, 과거형 권유)" — 둘 다 단일 grammar_point (106) 내 변형. compare_id `compare_n5_106_self` 또는 `compare_n5_106_variant` 형식 사용 가능. 수진 v2 작성 시 패턴 확정.

**정정 (2026-06-06, 수진 권한 위임 확정):** 수진이 v2 작성 시 `compare_n5_106_ta` 채택 (`_ta` = た形 접속 패턴 지칭, 수진 plan §125 + §130). 정빈님 ack (2026-06-06, "유지하고 츠쿠야에게 task 발송"). 본문의 `_self` / `_variant` 메모는 초안이며 실제 운영 값은 `_ta`.

**정밀화 (2026-06-06, 재현 02_workshop_plan §1 D-5 발견):** 수진 v2 schema md 도착 분석으로 자기 대조 쌍이 1쌍 (106_ta)이 아니라 **3쌍** 확인 — `compare_n5_031_031i` (ある/いる), `compare_n5_084_084i` (それから/そして), `compare_n5_106_ta` (ほうがいい). 모두 `left_grammar_point_id == right_grammar_point_id` 패턴. `left != right` CHECK 제약 절대 금지.

---

### [ARCH] E-17 — 정빈님 백지 재설계 채택 + 02_workshop_plan 결정 10건은 설계 원칙으로 보존

> 재현 `docs/planning/session_4/be_jaehyeon/02_workshop_plan.md` (275라인, 7 섹션) 정빈님 검토 결과. 정빈님이 lead 우회 재현 채널 직접 대화로 **방향 전환**.

**정빈님 인용 (2026-06-06, 직접 대화 채널, 재현 보고):**
> "DB가 너무 꼬였다. 패치 말고 백지에서 새로 짜자."
> "제가 다시 짜자고 했어요. 제가 이해가 안 가서, PM님도 있지만 결국 개발 총책임자는 저니까."

**결정 (lead 정정 ack 후):**
1. **`database_schema.md` 패치 방식 폐기** — D-1~D-10을 기존 스키마 위에 패치로 적용하지 않는다.
2. **백지 재설계** — DB는 새로 짠다.
3. **xlsx = 고정 입력 계약** — 데이터 표현은 동결, 어댑터(로더)가 정규화 흡수.
4. **N1~N5 공통 스키마** — N5 전용이 아니라 레벨 일반화.
5. **D-1~D-10 = 폐기 아님, 백지 재설계 target의 설계 원칙으로 보존** — chunk_type 정렬 / variant 단일 테이블 / JSONB 신설 / base only 참조 등은 백지로 짜도 그대로 좋은 설계.
6. **재설계 진입 시점**: 츠쿠야 재검수 도착 + 수진 후속 turn 일괄 정정 완료 후.

**기존 lead 진행 hold (재현 충돌 보고로 정정):**
- ❌ Migration 3 SQL 초안 lock — **hold** (재설계 target 위에서 재도출)
- ❌ `database_schema.md` D-6 (`diagnostic_questions` 추가) / D-7 (embedding_text 길이 스펙) 패치 — **hold** (새 문서로 흡수 가능, 패치하면 이중 작업)
- ✅ `glossary.md §9` connection_type enum 갱신 — 진행 가능 (영향 적음, 정책 일반)
- ✅ 한자/한글 통일 (수진 후속) / 츠쿠야 재검수 / 수진 D-9 source_pool — 재설계와 무관, 진행 가능 (단 D-9는 어댑터 계약 영향 가능성으로 재설계와 함께 처리 권고)

**Q2 통신 모드 정정 (정빈님 명시, 2026-06-06):**
> "Q2, 이건 그냥 제가 재현님 채널 가서 개인작업한다고 말씀드렸던 부분이구요."

→ **이번만**의 일회성 lead 우회. 기본은 정빈님 ↔ lead 단일 채널 유지 (CLAUDE.md §[TEAM] 그대로). 향후 운영 모드 변경 X.

**설계 원칙 10건 (백지 재설계 target에 보존):**

| ID | 설계 원칙 (보존) |
|---|---|
| D-1 | `chunk_type` enum = `point` / `compare` / `variant` 3종 (VARCHAR + 앱 Literal) |
| D-2 | variant → 단일 테이블 흡수 + `variant_of` 컬럼 (별도 테이블 X) |
| D-3 | comparison 2시트 → 단일 테이블 흡수 (메타는 JSONB) |
| D-4 | `border_meta JSONB` + `l3_tags JSONB` 양쪽 신설 (옵션 (i) — RAG 필터 강건) |
| D-5 | 자기 대조 3쌍 (031_031i / 084_084i / 106_ta) — `left==right` 허용, `left!=right` CHECK 금지 |
| D-6 | 진단 문제는 별도 테이블 (`diagnostic_questions` 또는 재설계 후 이름) |
| D-7 | `embedding_text` 길이 스펙 = point 150~270 / variant 120~150 / compare 50~100. DB CHECK 금지 |
| D-8 | `grammar_point_id` 참조 규약 = base point only |
| D-9 | `source_pool` JSON 통일 (배열 표기 일관, 어댑터 계약) |
| D-10 | variant `border_candidate` 3-state → BOOLEAN NULL 매핑 (미평가=NULL) |

**근거:**
- 정빈님이 "개발 총책임자로서" 직접 결정. 재현 페르소나 (Senior Backend / RAG)와 1:1 깊은 대화로 패치 한계 인식.
- D-1~D-10 = 패치 vs 재설계 무관하게 좋은 설계 → 보존.
- xlsx 고정 입력 계약 = 어댑터 책임 분리로 데이터-스키마 결합도 ↓.
- N1~N5 공통 스키마 = 재설계 한 번으로 차후 N2/N3/N1 진입 시 추가 마이그레이션 비용 ↓.

**영향 범위:**
- 재현 `02_workshop_plan.md` = "왜 패치로는 안 되는지" 입력 자료로 강등 (재현 자기 처리).
- 재현 후속: `03_redesign_*.md` 백지 설계 2장 (도메인 플로우 + target DB 모델, 레벨 일반화 + 어댑터 경계) 작성 예정 (츠쿠야 재검수 + 수진 후속 완료 후).
- 본 세션 마무리 흐름: 수진 후속 일괄 처리 → N5 안정화 완료 선언 → 백지 재설계 진입.
- 운영 통신: 정빈님 ↔ lead 단일 채널 유지 (Q2 명확화).

---

### [PROCESS] E-17-부속 — 본 E-17 본문 변경 이력 (lead 운영 메모)

본 E-17은 2026-06-06 lead가 1차로 "D-1~D-10 패치 적용 정빈님 일괄 ack" 형식으로 추기했다가, 같은 날 재현 충돌 보고 + 정빈님 직접 명확화로 "백지 재설계 채택 + 설계 원칙 보존" 톤으로 정정. lead 정보 비대칭 사례.

**향후 운영 정정 후보 (CLAUDE.md §과거 실패 통합 검토):**
- 정빈님이 lead 우회 팀원 채널 직접 대화 시 → 팀원이 즉시 lead에 충돌 보고 (재현 패턴 정착, AGENTs.md §범위 규율 활용 성공 사례).
- lead는 충돌 보고 받으면 정빈님께 한 줄 확인 (lead 단독 진행 금지).

| ID | 결정 | 게이트 | ack 결과 | 처리 |
|---|---|---|---|---|
| **D-1** | `chunk_type` enum 정렬 → `point`/`compare`/`variant` 3종 (DB는 VARCHAR + 앱 Literal 갱신) | 🔴 스키마 | A 정렬 | Migration 3 (앱 코드) |
| **D-2** | variant → `grammar_chunks` + `variant_of VARCHAR(100) NULL` 단일 테이블 흡수 | 🔴 스키마 | A 흡수 | Migration 3 |
| **D-3** | comparison 2시트 → `grammar_chunks(chunk_type='compare')` 흡수 (메타는 `content` JSONB) | 🟢 설계 | A 흡수 | 로더 매핑 (트랙 3) |
| **D-4** | `border_meta JSONB` + **`l3_tags JSONB`** 양쪽 신설 (옵션 (i) — RAG 필터 강건) | 🔴 스키마 | (i) 신설 | Migration 3 |
| **D-5** | 자기 대조 3쌍 (031_031i / 084_084i / 106_ta) — `left==right` 허용, `left!=right` CHECK 금지 | ✅ 인지 | 확정 | Migration 3 (CHECK 미추가) |
| **D-6** | `database_schema.md`에 `diagnostic_questions` 추가 (문서 드리프트 해소) | 🟡 문서 | A 추가 | lead 갱신 |
| **D-7** | `embedding_text` 길이 스펙 갱신 (§15-3): point 150~270 / variant 120~150 / compare 50~100. DB CHECK 금지 | 🟢 문서 | A 갱신 | lead 갱신 |
| **D-8** | `grammar_point_id` 참조 규약 = **base point only** (learning/weak_points는 variant·compare ID 미참조) | 🟡 규약 | A | 서비스 레이어 명문화 (트랙 3) |
| **D-9** | `source_pool` CSV vs `comparison_pair_ids` JSON 혼재 → **JSON 통일** | 🟡 데이터/로더 | A 통일 | **수진 후속 task 묶음** (한자/한글 + §8 stale 함께, 츠쿠야 재검수 후) |
| **D-10** | variant `border_candidate` 3-state (`True`/`False`/`미결`) → `border_flag BOOLEAN NULL` 허용 (`미결`=NULL 매핑) | 🔴 스키마 | A NULL 매핑 | Migration 3 |

**Migration 3 SQL 초안 (재현 plan §2 lock, 실제 적용은 별도 정빈님 ack 필수):**
```sql
ALTER TABLE grammar_chunks
  ADD COLUMN variant_of VARCHAR(100) NULL,
  ADD COLUMN border_meta JSONB NULL,
  ADD COLUMN l3_tags JSONB NULL,
  ALTER COLUMN border_flag DROP NOT NULL;
```

**근거:**
- 정빈님 ack (2026-06-06): "그렇게 하고, 한글 통일, 그리고 얼른.. 데이터 검수 다 받고 정규화 할 수 있도록.."
- 재현 plan §0 결론: v2 데이터 변화(109/3/25)는 마이그레이션 순서·테이블 수를 흔들지 않는다. 영향은 `grammar_chunks` 단일 테이블 컬럼 + 로더로 수렴.
- 11 테이블 유지 (D-2 흡수 채택으로 variant 별도 테이블 비채택).
- D-4 (i) 채택 근거 — RAG 필터 강건성 우선, 향후 query 효율 ↑. 최소주의보다 데이터 활용도 우선.

**영향 범위:**
- Migration 3 SQL 초안 = 재현 plan §2 (실제 적용은 별도 정빈님 ack).
- `database_schema.md` 갱신 (D-6 / D-7) — lead 처리, 본 세션 진입.
- `glossary.md §9` connection_type enum 갱신 (cross-track #5) — lead 처리.
- 트랙 3 (적재 스크립트) 진입 readiness — 츠쿠야 재검수 + 수진 후속 task 완료 후.
- 다음 단계: 정빈님 별도 ack로 Migration 3 적용 → 적재 스크립트 → Stage 1 (스키마 적재).

**Cross-track 발견 6건 처리 매핑** (재현 plan §4):
- #1 수진 plan §8 stale (110/22) → 수진 후속 task 묶음 (D-9와 함께)
- #2 compare_id `_ta` → 본 세션 처리 완료
- #3 절 번호 역순 → 무시
- #4 source_pool 혼재 → D-9
- #5 glossary §9 connection_type stale → lead 갱신
- #6 variant border 한글 `미결` → D-10

---

### [ARCH] E-18 — 재현 백지 재설계 target 12 테이블 lock + ORM/Alembic 검증 통과 (2026-06-08)

> 정빈님 직접 위임으로 재현이 §7 6 논점을 단독 lock 후 target 설계 + ORM + Alembic 마이그레이션 + 컨테이너 검증까지 일괄 완료. 본 항목은 lead 사후 등록 (재현 사후 보고 4건 기반).

**정빈님 인용 (2026-06-06, 재현 채널 직접 대화 사후 보고):**
> "재현이 깔끔한 구조+데이터형식 문서 만들고 DB까지 짜두라."

**결정:**

#### 1. target 12 테이블 lock (11 → 12)
| # | 테이블 | 도메인 | 비고 |
|---|---|---|---|
| 1 | `chunks` ⭐ | 콘텐츠 | point/compare/variant 통합 + 임베딩 (RAG 원본) |
| 2 | `comparison_pairs` | 콘텐츠 | 비교쌍 트리거 seed (신설, +1) |
| 3 | `anonymous_sessions` | 진단 | 익명 세션 (계승) |
| 4 | `diagnostic_sessions` | 진단 | 진단 흐름 (계승) |
| 5 | `diagnostic_questions` | 진단 | 진단 문제 seed (D-6 신설) |
| 6 | `diagnostic_answers` | 진단 | 문항별 답안 (계승) |
| 7 | `users` | 학습 | 회원 (계승) |
| 8 | `learning_sessions` | 학습 | 학습 흐름 (계승) |
| 9 | `learning_records` | 학습 | 숙련도 누적 (계승) |
| 10 | `weak_points` | 학습 | 취약 포인트 (계승) |
| 11 | `last_session` | 학습 | 이어하기 (계승) |
| 12 | `llm_response_cache` | 캐시 | LLM 캐시 (계승) |

#### 2. 단일 진실 정리본
**`docs/planning/session_4/be_jaehyeon/00_db_overview.md`** (재현 작성, 2026-06-08). 변천 기록 (`03_redesign_sketch` / `04_target_db_design` / `05_schema_reference`)은 보존.

#### 3. §7 6 논점 lock (재현 자율 lock, 정빈님 위임 확정)
- 테이블명 → `chunks`
- 단일 테이블 흡수 → point/compare/variant
- `comparison_pairs` seed 분리 (트리거 진실)
- taxonomy = 앱 상수 (테이블 아님)
- 진단 문제 = DB 테이블 (`diagnostic_questions`)
- 기존 문서 처리 = 변천 기록 보존

#### 4. ORM 12 + Alembic 골격 + 초기 마이그레이션
- `src/db/models/{base, content, diagnostic, learning, cache}.py`
- `src/db/migrations/versions/0001_initial_schema.py` (revision `0001`, `vector` + `pgcrypto` 확장 포함)
- `tests/test_models.py` (단위 테스트 5/5 통과)

#### 5. 컨테이너 검증 통과
- 임시 pgvector/pg16 컨테이너 — metadata ↔ DB 컬럼 전수 일치
- 타입 (embedding=vector, body=jsonb) / FK 9건 (순환 2, use_alter) / CHECK 4 / 부분 인덱스 정상
- 자기 대조 insert (left == right) 통과 / 잘못된 chunk_type 거부 정상
- 검증 컨테이너 제거 완료 (프로젝트 docker-compose 미변경)

#### 6. 어댑터 계약 5선 (재설계 핵심)
1. `source_pool` `"SRC-01,02,..."` → `["SRC-01", ...]` JSON 배열 확장 (D-9 자연 해소)
2. `comparison_pair_ids` = `comparison_pairs` seed에서 단방향 도출 (l3 저장 X, 양방향 수동 동기화 제거)
3. variant `border_candidate` `"미결"` → `NULL` (D-10 자연 소멸 — variant 전부 FALSE 확정)
4. `star_weight` `"3star"` → SMALLINT `3`
5. `taxonomy` `item_count` 재계산 (드리프트 차단, F2 인풋 해소)

#### 7. 잔여 게이트 (정빈님 결정 대기)
- dev 의존성 추가 (`poetry add --group dev pytest pytest-asyncio mypy ruff greenlet`) + pyproject 선언 보강 (CLAUDE.md §[VERIFY] 정합)
- `alembic upgrade head` 실 적용
- 어댑터 적재 `scripts/load_chunks.py` 진입 (수진 후속 동결 완료 ✅, 즉시 가능)

**근거:**
- 재현 readiness `01_readiness_check.md` §5 D-1~D-8 + 워크숍 plan `02_workshop_plan.md` D-9·D-10 + 백지 재설계 원칙 3건 (level 1급 / xlsx 고정입력 / 단일 진실 + 파생 뷰) → target 설계로 통합.
- 도메인 9개 테이블은 `database_schema.md §5~14` 설계 건강 → 계승 (재설계 범위 = chunks + 어댑터 + 레벨 일반화에 한정).
- xlsx F1·F2 드리프트 클래스 → 어댑터 정규화로 구조적 제거 (재현 03 인풋 3 = 단일 진실 + 파생 뷰 원칙).

**영향 범위:**
- `database_schema.md` 전면 갱신 (`grammar_chunks` → `chunks` 12 테이블, 재현 00 입력) — lead 처리 (본 ack 묶음)
- `glossary.md §12` MVP 11 → 12 정정 — ✅ 완료
- `implementation_roadmap.md` 어댑터 명칭 + 스크립트 명칭 + N5 84 → 109 갱신 — lead 처리
- `data_pipeline.md` JSON 흐름 → xlsx 어댑터 갱신 — lead 처리
- `local_dev_setup.md` 스크립트 명칭 갱신 — lead 처리
- `project_summary.md §0·§2-3` 재설계 범위 좁힘 반영 — lead 처리 (본 ack 묶음)

**Cross-track:**
- D-9 (source_pool JSON 통일) = 어댑터 정규화 5선에 포함, 자연 해소
- D-10 (variant border 3-state) = 츠쿠야 §6 판정으로 variant 전부 FALSE 확정, 자연 소멸 (단 `border_flag BOOLEAN NULL` 허용은 향후 확장 여지로 유지)
- D-6 (`diagnostic_questions` 추가) = 본 target에 신설로 반영, `database_schema.md` 패치 자동 흡수
- D-7 (`embedding_text` 길이 스펙) = 본 target에 직접 반영 (point 150~270 / variant 120~150 / compare 50~100, CHECK 미추가)

---

## 미결 및 상태 (임시)
> 단일 진실 = `decision_log.md` (본 파일) + `glossary.md` + `docs/planning/session_N/pm_minseok/summary.md`. (구 `projectState.json`은 2026-06-06 세션 4에서 삭제 — stale 누적 + 위 3종으로 대체.)

- 아직 확정되지 않은 결정은 각 문서의 **미결 및 상태** 섹션에 있습니다.
- 결정이 내려지는 대로 이 로그에 **[카테고리] 제목**으로 추가합니다.
- 기존 결정을 번복할 때는 삭제하지 않고 **새 날짜의 항목**으로 번복 내역을 기록합니다 (예: "2026-04-10의 [DATA] 결정을 아래와 같이 수정"). 본문 정정 시 정정 이력을 본 항목에 명시 (E-16, E-17 부속 참조).