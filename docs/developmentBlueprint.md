# 개발 골격 초안

> 최종 업데이트: 2026-04-14
> 현재 제품 구상을 실제 구현 순서로 바꿔 정리한 초안 문서입니다.

---

## 1. 목표

이 프로젝트의 Phase 1 목표는 아래를 실제로 동작시키는 것입니다.

1. 사용자의 문법 레벨을 진단한다.
2. 약한 문법 포인트를 뽑아낸다.
3. Retrieval 기반으로 문법 설명을 제공한다.
4. 간단한 학습 루프를 세션 단위로 이어간다.

즉, Phase 1은 문서 정리가 아니라 “직접 돌려볼 수 있는 데모”까지 가야 합니다.

---

## 2. 개발 방향

가장 안전한 순서는 아래와 같습니다.

1. 저장소 골격을 먼저 안정화한다.
2. 얇지만 끝까지 이어지는 백엔드 한 줄기를 먼저 만든다.
3. 그 위에 retrieval과 임베딩을 붙인다.
4. 그 다음에 LangGraph 워크플로우를 얹는다.
5. 마지막에 UI를 붙인다.

초반부터 모든 레이어를 동시에 크게 벌리면 복잡도만 올라갑니다.

---

## 3. 목표 시스템 형태

```text
클라이언트
  └─ Streamlit 데모 UI

백엔드
  └─ FastAPI
     ├─ 세션 엔드포인트
     ├─ 진단 엔드포인트
     ├─ 추천 엔드포인트
     └─ 학습 엔드포인트

애플리케이션 계층
  ├─ 진단 서비스
  ├─ 학습 서비스
  ├─ 추천 서비스
  ├─ retrieval 서비스
  └─ llm 서비스

에이전트 계층
  └─ LangGraph 워크플로우
     ├─ 학습 상태 분석
     ├─ 문법 청크 retrieval
     ├─ 설명 생성
     └─ 정오답에 따른 분기

저장 계층
  ├─ PostgreSQL 16
  │  ├─ 애플리케이션 테이블
  │  └─ pgvector 기반 임베딩
  └─ Redis
     └─ 응답 캐시 / 임시 세션 지원
```

---

## 4. 권장 저장소 골격

```text
training_jlpt/
├── src/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── sessions.py
│   │   │   ├── diagnosis.py
│   │   │   ├── recommendations.py
│   │   │   └── learning.py
│   │   ├── schemas/
│   │   └── dependencies/
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   ├── models/
│   │   ├── repositories/
│   │   └── migrations/
│   ├── services/
│   │   ├── sessions.py
│   │   ├── diagnosis.py
│   │   ├── recommendations.py
│   │   ├── learning.py
│   │   ├── retrieval.py
│   │   ├── embeddings.py
│   │   └── llm.py
│   ├── agent/
│   │   ├── graph.py
│   │   ├── state.py
│   │   └── nodes/
│   └── scripts/
│       ├── seedDiagnosisQuestions.py
│       ├── importGrammarChunks.py
│       └── embedGrammarChunks.py
├── data/
│   ├── raw/
│   ├── curated/
│   └── generated/
├── tests/
│   ├── api/
│   ├── services/
│   └── integration/
├── docs/
└── projectState.json
```

---

## 5. 개발 순서

### Stage 0. 기반 골격

목표:
저장소를 실제 실행 가능한 상태로 만든다.

산출물:

- `src/`, `tests/`, `data/` 기본 디렉토리 생성
- FastAPI 앱 엔트리포인트 생성
- `.env` 기반 설정 로더 생성
- DB 연결과 Redis 클라이언트 연결 준비
- SQLAlchemy 기본 모델 구조 생성
- Alembic 초기화 계획 수립

완료 기준:
`GET /health`가 로컬에서 동작하고 Docker 서비스와 연결된다.

---

### Stage 1. 진단 수직 슬라이스

목표:
사용자가 실제로 처음 가치를 느끼는 가장 작은 흐름을 완성한다.

범위:

- 익명 세션 생성
- 진단 세션 시작
- 문제 조회
- 답안 제출
- 진단 완료
- 약점 포인트 추출

필요 데이터:

- MVP용 고정 진단 문제 세트
- 각 문제에 연결된 grammar point 식별자

완료 기준:
신규 사용자가 진단을 끝내고 레벨과 약점 포인트를 받을 수 있다.

---

### Stage 2. 학습 코어

목표:
약점 포인트를 실제 학습 세션으로 연결한다.

범위:

- 다음 문법 포인트 추천
- 학습 세션 시작
- 문법 청크 조회
- 설명 생성
- 확인 문제 1개 생성
- 답안 결과 저장

완료 기준:
진단 결과에서 바로 한 번의 학습 루프를 돌릴 수 있다.

---

### Stage 3. Retrieval 및 임베딩 파이프라인

목표:
하드코딩된 설명 대신 retrieval 기반 설명으로 전환한다.

범위:

- `grammar_chunks` 테이블 정의
- 정제된 청크 데이터 PostgreSQL 적재
- `text-embedding-3-small`로 임베딩 생성
- `pgvector`에 벡터 저장
- 메타데이터 필터 기반 검색 구현

완료 기준:
문법 설명이 하드코딩 데이터가 아니라 실제 retrieval 결과를 사용한다.

---

### Stage 4. LangGraph 통합

목표:
분기 로직을 서비스 코드에서 분리해 명시적인 워크플로우로 옮긴다.

범위:

- 학습 상태 객체 정의
- retrieve node
- explain node
- quiz node
- branch node
- 오답 시 재설명 경로

완료 기준:
학습 루프가 그래프 형태로 추적 가능해진다.

---

### Stage 5. 데모 UI

목표:
외부인이 직접 써볼 수 있는 MVP 화면을 만든다.

범위:

- Streamlit 온보딩 화면
- 진단 화면
- 진단 결과 화면
- 학습 세션 화면
- 이어하기 화면

완료 기준:
백엔드 코드를 읽지 않아도 데모를 직접 체험할 수 있다.

---

## 6. 우선 구현할 데이터 모델

우선순위는 아래 순서가 적절합니다.

1. `users`
2. `anonymous_sessions`
3. `diagnostic_sessions`
4. `diagnostic_answers`
5. `learning_sessions`
6. `learning_records`
7. `grammar_chunks`
8. `weak_points`
9. `llm_response_cache`
10. `last_session`

메모:

- `anonymous_sessions`는 문서상 개념이 아니라 실제 테이블이나 저장 구조로 확정하는 게 좋습니다.
- `grammar_chunks`에는 level, grammar point, chunk type, source status 같은 retrieval 메타데이터가 필요합니다.
- `llm_response_cache`는 나중에 붙이더라도 구조는 초기에 잡아두는 편이 좋습니다.

---

## 7. 에이전트별 적정 역할

### 민석

- Phase 1 범위 고정
- 인증 범위 결정
- 데모 완료 기준 승인

### 수진

- grammar point ID 체계 확정
- N5 청크 스키마 확정
- 진단 문제 원본 세트 준비

### 츠쿠야

- 생성 문법 데이터 검수 기준 정의
- 설명 품질 검토
- 진단 문항 문구 검토

### 재현

- 백엔드와 인프라 구현
- 저장 구조와 retrieval 파이프라인 설계
- LLM, LangGraph 통합

현재 역할 분담은 이 정도면 충분히 workable 합니다.
다만 각 단계마다 파일 단위 산출물이 있어야 실제로 협업이 굴러갑니다.

---

## 8. 꼭 필요한 핸드오프 산출물

멀티 에이전트 협업이 실제로 작동하려면 상태 업데이트만으로는 부족합니다.
핸드오프는 반드시 파일이나 스키마 형태로 끝나야 합니다.

예시:

- 수진 -> 재현: `data/curated/n5GrammarChunks.json`
- 수진 -> 재현: `data/curated/diagnosisQuestions.json`
- 츠쿠야 -> 팀: `docs/validationChecklist.md`
- 민석 -> 팀: `docs/mvpScope.md`
- 재현 -> 팀: API 스키마, DB 스키마, import script

파일 기반 산출물이 없으면 현재 핸드오프 구조는 쉽게 흔들립니다.

---

## 9. 초기에 꼭 잠가야 할 결정

아래 항목은 Stage 1 전이나 초반에 확정하는 게 좋습니다.

1. Phase 1은 닉네임 기반만 지원할지, 로그인까지 포함할지
2. 익명 세션을 Redis에 둘지, PostgreSQL에 둘지, 둘 다 쓸지
3. grammar point ID 포맷을 무엇으로 할지
4. grammar chunk JSON 스키마를 어떻게 정의할지
5. 진단 점수를 완전 규칙 기반으로 할지, 일부 LLM 보조를 허용할지

---

## 10. 가장 현실적인 다음 스프린트

지금 바로 구현을 시작한다면 다음 스프린트는 아래에만 집중하는 게 좋습니다.

1. `src/`, `tests/`, `data/` 골격 생성
2. FastAPI 앱과 `GET /health` 구현
3. 세션, 진단, grammar chunk 관련 SQLAlchemy 모델 초안 작성
4. `pgvector` extension 포함한 초기 마이그레이션 준비
5. `apiEndpoints.md` 기준 진단 API 구현 시작
6. 진단 문제 seed script 초안 작성

이 순서가 가장 효율적인 이유는, 문서 중심 상태를 실행 중심 상태로 가장 빨리 전환할 수 있기 때문입니다.

---

## 11. 현재 준비도 평가

### 강점

- 제품 동기가 분명합니다.
- Phase 1 범위가 대체로 읽힙니다.
- 벡터 검색 기준이 `pgvector`로 정리됐습니다.
- 역할 경계가 개념상으로는 적절합니다.

### 약점

- 실제 저장소 골격이 아직 없습니다.
- 핸드오프가 파일 산출물보다 상태 업데이트 중심입니다.
- 상태 파일이 참조하는 작업 디렉토리와 프롬프트 자산이 아직 부족합니다.
- 검수 기준 문서가 아직 충분히 구체적이지 않습니다.

### 결론

이 프로젝트는 구현 계획 단계로는 충분히 준비됐습니다.
하지만 멀티 에이전트가 매끄럽게 굴러가려면 한 번 더 실행 골격 세팅이 필요합니다.
