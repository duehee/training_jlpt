# 데이터 파이프라인

> 최종 업데이트: 2026-06-08 (재설계 후 xlsx 어댑터 패턴 반영)
> 담당 축: **Data** — 학습 데이터를 어떻게 확보하고 검증하는가
> 관련 문서: `database_schema.md`, `decision_log.md`, `agent_guide.md`, `implementation_roadmap.md`
>
> 재설계 변경 (E-18, 2026-06-08):
> - 구 JSON 흐름 (`data/generated/*.json`, `data/curated/*.json`) → **xlsx 고정 입력 계약** (`data/{level}/*.xlsx` + `data/schema/*.md`)
> - 구 `chunks` → **`chunks`** (point/compare/variant 통합)
> - 어댑터 (`scripts/load_chunks.py`)가 xlsx 정규화 5선 (CSV→JSON / 미결→NULL / star 정수화 / pair 도출 / item_count 재계산) 흡수
> - 단일 진실: `docs/planning/session_4/be_jaehyeon/00_db_overview.md` §2·§9

---

## 📌 빠른 참조 (에이전트용)

**이 문서에서 찾을 수 있는 것**
- 데이터 소스 전략 (오픈데이터 + LLM + 검수) → 1장
- 데이터 소스별 라이선스 정리 → 2장
- 청크 생성 워크플로우 (9단계) → 3장
- 단계별 산출물과 책임 에이전트 → 4장
- 검수 3단 레이어 구조 → 5장
- LLM 배치 생성 정책 → 6장
- 데이터 디렉토리 구조 → 7장
- 데이터 버전 관리 정책 → 8장
- 비용 관리 (LLM API 호출) → 9장

**이 문서에서 찾을 수 없는 것**
- 청크 JSON 구조 → `database_schema.md` 15장
- BORDER 23개 항목 목록 → 데이터 자체 (`data/curated/`) 또는 츠쿠야 prompt
- 츠쿠야 검증 체크리스트 11개 → `prompts/jp_tsukuya_prompt.md` 또는 추후 `validation_checklist.md`
- API 엔드포인트 → `api_endpoints.md`
- 구현 일정 → `implementation_roadmap.md`

---

## 이 문서는
JLPT 개인 학습 에이전트의 **학습 데이터 확보 및 검증 파이프라인**을 정의합니다.
"데이터를 어디서 얻고, 누가 만들고, 어떻게 검증하고, 어디에 저장하는가"의 단일 기준입니다.

**데이터 품질이 RAG 결과의 품질을 결정**하므로, 이 파이프라인의 일관성이 곧 서비스 품질입니다.

---

## 1. 데이터 소스 전략

핵심 원칙: **"뼈대는 오픈데이터, 살은 LLM, 검증은 별도 에이전트"**

### 1-1. 3계층 구조

```
[오픈데이터]
  └─ 사실 정보 (문법명, 레벨)만 참고
       ↓
[LLM 생성]
  └─ 의미 설명, 접속 규칙, 예문, 혼동 문법 등 생성
       ↓
[에이전트 검수]
  └─ 츠쿠야 체크리스트 11개 항목으로 검증
```

### 1-2. 왜 이 구조인가

| 이유 | 설명 |
|------|------|
| 저작권 보호 | 오픈데이터 사이트의 설명/예문은 직접 사용하지 않고 LLM으로 자체 생성 |
| 편향 방지 | LLM 단독 검수 시 같은 모델 편향 위험 → 별도 에이전트가 체크리스트로 검증 |
| 비용 효율 | 사람이 처음부터 작성하지 않고 LLM 배치 생성 + 샘플링 검수로 처리 |
| 면접 답변 가치 | "데이터 품질 관리 체계"를 명확히 설명 가능 (포트폴리오 강점) |

### 1-3. 절대 원칙

- **JLPT 기출문제는 직접 사용하지 않는다.** 저작권 위반.
- **오픈데이터 사이트의 설명/예문은 가져오지 않는다.** 목록(사실 정보)만 참고.
- **모든 LLM 생성 데이터는 자체 데이터로 취급**하되, 출처는 `source` 필드에 기록.
- **데이터 소스의 라이선스를 반드시 확인**하고 2장에 기록한다.

---

## 2. 데이터 소스별 라이선스

| 소스 | 라이선스 | 사용 범위 | 비고 |
|------|---------|----------|------|
| **jlptsensei.com** | (서비스 이용약관) | 문법 목록 + 레벨 분류만 참고 | 설명·예문은 가져오지 않음 |
| **Tatoeba** | CC BY 2.0 | 예문 보충용 | LLM 생성 예문이 부자연스러울 때 교체 검토 |
| **JMdict** | CC BY-SA 3.0 | 어휘 데이터 | Phase 2 어휘 영역 도입 시 활용 검토 |
| **GitHub JLPT 어휘 리포지토리** | 리포지토리별 상이 | 어휘 데이터 | Phase 2 도입 시 라이선스 개별 확인 |
| **OpenAI (GPT-4o-mini, GPT-4o)** | 상업적 사용 가능 | 모든 청크 콘텐츠 생성 | API 비용 발생 |
| **OpenAI (text-embedding-3-small)** | 상업적 사용 가능 | 임베딩 생성 | API 비용 발생 |

### 2-1. Tatoeba 활용 정책

- LLM 생성 예문이 어색하다고 판단된 경우에만 교체.
- 교체 시 `examples[].source: "tatoeba"` 추가 (현재 스키마에 없으면 보강 검토).
- 라이선스 표기는 데이터셋 단위로 한 번만 명시 (개별 예문에는 불필요).

### 2-2. 향후 도입 검토 (Phase 2~3)

- **JMdict**: Phase 2 어휘 학습 도입 시
- **NHK Easy Japanese**: 독해 청크 도입 시 (라이선스 재검토 필요)
- **JLPT 공식 자료**: 사용 불가. 기출 패턴 분석은 자체 추정.

---

## 3. 청크 생성 워크플로우

오픈데이터 목록부터 벡터DB 적재까지의 **9단계 표준 흐름**입니다.

```
1. 오픈데이터 목록 참고 (jlptsensei 등)
        ↓
2. 수진: 레벨 기준표 + BORDER 플래그 작성 (LLM 필드 비워둠)
        ↓
3. 츠쿠야: 기준표 검수
        ↓
4. 민석: 확정 판단 (BORDER 등 레벨 배정 최종)
        ↓
5. 수진: LLM 필드 샘플 5개 생성 (프롬프트 템플릿용)
        ↓
6. 츠쿠야: 샘플 검수 (체크리스트 11개)
        ↓
7. 재현: 배치 생성 스크립트 작성 (샘플=프롬프트 템플릿)
        ↓
8. 재현: LLM 배치 생성 → 결과 저장
        ↓
9. 츠쿠야: 배치 결과 샘플링 검수
        ↓
[검수 통과] → 재현: PostgreSQL 적재 + 임베딩 생성 → pgvector 인덱싱
```

### 3-1. 단계별 게이트

각 단계는 **다음 단계로 넘어가기 위한 조건**이 있습니다.

| 단계 | 다음 진행 조건 |
|------|--------------|
| 1→2 | 오픈데이터에서 N5/N4/N3 목록 확보 |
| 2→3 | 기준표(엑셀/JSON) 완성 + BORDER 플래그 표기 |
| 3→4 | 츠쿠야 검수 의견 정리 |
| 4→5 | 민석의 명시적 확정 (decisionLog 기록) |
| 5→6 | LLM 샘플 5개 JSON 작성 완료 |
| 6→7 | 샘플 검수 ✅ 4건 이상 (5건 중) |
| 7→8 | 배치 스크립트 dry-run 통과 |
| 8→9 | 배치 결과 JSON 파일 생성 |
| 9→적재 | 샘플링 검수 통과율 ≥ 80% |

### 3-2. 게이트 미통과 시

- **샘플 검수 ⚠️ 또는 ❌**: 수진이 수정 후 6단계 재진행
- **배치 결과 검수 < 80%**: 프롬프트 템플릿 재조정 후 7단계 재진행
- **레벨 배정 충돌**: 민석에게 에스컬레이션 (4단계 재진행)

---

## 4. 단계별 산출물과 책임 에이전트

각 단계가 끝났을 때 어떤 파일이 어디에 만들어져야 하는지 정의합니다.
**파일이 없으면 단계가 완료되지 않은 것**입니다.

| 단계 | 책임 | 산출물 경로 | 포맷 |
|------|------|-------------|------|
| 2 | 수진 | `data/raw/{level}_grammar_list.xlsx` | 엑셀 (목록 + 메타) |
| 2 | 수진 | `data/raw/{level}_border_flags.json` | JSON 배열 |
| 2 | 수진 | `data/raw/{level}_compare_pairs.json` | JSON 배열 (혼동 쌍) |
| 5 | 수진 | `data/curated/{level}_llm_sample.json` | JSON 배열 (5건) |
| 6 | 츠쿠야 | `data/curated/{level}_llm_sample_review.md` | 검수 결과 마크다운 |
| 7 | 재현 | `src/scripts/generate_chunks.py` | 파이썬 스크립트 |
| 8 | 재현 | `data/generated/{level}_chunks.json` | JSON 배열 (전체) |
| 8 | 재현 | `data/generated/{level}_compare_chunks.json` | JSON 배열 (전체) |
| 9 | 츠쿠야 | `data/generated/{level}_review_sample.md` | 검수 결과 마크다운 |
| 적재 | 재현 | DB row insert + embedding 생성 | DB 적용 |
| 적재 | 재현 | `data/curated/{level}_chunks.json` | **확정본** (적재 성공 후) |

### 4-1. 디렉토리 의미

- `data/raw/`: 가공 전 원본 (목록, 기준표)
- `data/generated/`: LLM 배치 생성 직후 (검수 전)
- `data/curated/`: **검수 완료 + DB 적재 완료된 확정본**

### 4-2. 핵심 규칙

- **`curated/` 파일은 변경 시 반드시 재검수 + 재임베딩**
- **`generated/` 파일은 검수 통과 후 `curated/`로 승격**
- **모든 산출물 JSON은 UTF-8, 들여쓰기 2 스페이스**

---

## 5. 검수 3단 레이어 구조

데이터 검증의 핵심 안전 장치입니다.

### 5-1. 3단 레이어

| 레이어 | 역할 | 누가 | 산출물 |
|--------|------|------|-------|
| **L1: 오픈데이터** | 사실 정보(목록/레벨) 신뢰성 확보 | 수진 (수집) | 기준표 |
| **L2: LLM 생성** | 콘텐츠 자체 생성 | 수진 (샘플) + 재현 (배치) | 청크 JSON |
| **L3: 에이전트 검수** | 체크리스트 기반 품질 검증 | 츠쿠야 | 검수 결과 |

### 5-2. 왜 3단이 필요한가

`decision_log.md` 2026-04-10 항목 참조.

- L1 단독: 저작권 위반 + 콘텐츠 부족
- L2 단독: LLM 환각 + 검증 불가
- L3 단독: 검증할 콘텐츠 자체가 없음
- L2 + L2: 같은 모델 편향 (검증 독립성 부재)

→ **3단이 모두 있어야** 저작권/품질/독립성을 동시에 만족.

### 5-3. 츠쿠야 검수 체크리스트

11개 항목의 상세 체크리스트는 `prompts/jp_tsukuya_prompt.md` 4장에 있습니다.
별도 `docs/validation_checklist.md`로 분리 예정 (`agent_guide.md` 미결).

요약:
- 문법 청크 7개 항목 (레벨/의미/접속/예문 4종)
- 비교 청크 추가 4개 항목 (대조 명확성/실수 구체성/번역 차별성/어휘 범위)

### 5-4. 판정 결과 처리

| 판정 | 처리 |
|------|------|
| ✅ 승인 | `data/curated/`로 승격 후 DB 적재 |
| ⚠️ 수정 요청 | 수진에게 반환, 수정 후 재검수 |
| ❌ 반려 | 전면 재작성 (LLM 프롬프트 재검토) |

---

## 6. LLM 배치 생성 정책

수진의 샘플 5개를 기반으로 재현이 작성하는 **배치 생성 스크립트**의 운영 정책입니다.

### 6-1. 기본 원칙

- **샘플 5개를 프롬프트 템플릿으로** 활용 (few-shot 방식)
- **일괄 처리는 N=10 단위**로 청크 처리 (실패 격리)
- **재시도는 최대 3회**, 그 이상 실패 시 수동 검토 큐로
- **모든 호출 로그 기록** (`data/generated/_logs/`)

### 6-2. 모델 선택

| 용도 | 모델 | 근거 |
|------|------|------|
| 청크 생성 (기본) | `gpt-4o-mini` | 비용 효율 (decisionLog 2026-04-14) |
| 청크 생성 (품질 필요) | `gpt-4o` | 비교 청크 등 뉘앙스 중요할 때 |
| 임베딩 | `text-embedding-3-small` | 다국어 크로스링구얼 |

### 6-3. 프롬프트 템플릿 구조

```
[시스템 프롬프트]
- 츠쿠야 체크리스트 기준을 사전 만족하도록 지시
- 출력은 JSON 형식으로 강제
- 한국어 의미, 일본어 예문 명시

[Few-shot 예시]
- 수진의 샘플 5개를 input/output 쌍으로 삽입

[실제 입력]
- 문법 포인트명 + 레벨 + BORDER 여부
```

### 6-4. 출력 검증 (1차 자동)

배치 스크립트 자체에서 아래를 자동 검증:

- [ ] JSON 파싱 가능
- [ ] 필수 필드 (`point`, `meaning_ko`, `connection`, `examples`) 존재
- [ ] `examples` 배열 길이 ≥ 2
- [ ] `embedding_text` 길이 40~80자

자동 검증 실패 시 → 재시도 → 그래도 실패 시 → 수동 검토 큐.

### 6-5. 재임베딩 정책

`embedding_text` 변경 감지 시:

```
변경 감지 → 새 embedding 생성 → 같은 row UPDATE → 단일 트랜잭션
```

상세는 `database_schema.md` 13장 동기화 흐름 참조.

---

## 7. 데이터 디렉토리 구조

```
data/
├── raw/                       가공 전 원본
│   ├── n5_grammar_list.xlsx
│   ├── n5_border_flags.json
│   ├── n5_compare_pairs.json
│   ├── n4_grammar_list.xlsx (예정)
│   └── ...
├── curated/                   확정본 (검수 + DB 적재 완료)
│   ├── n5_chunks.json
│   ├── n5_compare_chunks.json
│   ├── n5_llm_sample.json
│   ├── n5_llm_sample_review.md
│   ├── diagnosis_questions.json
│   └── ...
├── generated/                 LLM 배치 생성 직후 (검수 전)
│   ├── n5_chunks.json
│   ├── n5_compare_chunks.json
│   ├── n5_review_sample.md
│   └── _logs/                 배치 호출 로그
│       └── 2026-04-20_batch_001.jsonl
└── README.md                  이 디렉토리 사용 규칙
```

### 7-1. `data/README.md` 권장 내용

- 디렉토리 구조 한 줄 설명
- 각 단계별 산출물 위치 안내
- 절대 변경 금지 파일 목록 (`curated/` 전체)

### 7-2. Git 정책

| 디렉토리 | Git 추적 |
|---------|---------|
| `data/raw/` | 추적 (원본 보존) |
| `data/curated/` | 추적 (확정본 보존) |
| `data/generated/` | 추적 안 함 (`.gitignore`) — 재생성 가능 |
| `data/generated/_logs/` | 추적 안 함 (`.gitignore`) |

**이유**: `generated/`는 LLM 호출 결과라 비결정적 + 용량이 큼. 검수 통과 후 `curated/`로 승격된 것만 보존.

---

## 8. 데이터 버전 관리 정책

### 8-1. 청크 단위 버전

`chunks.metadata` JSONB에 버전 정보 기록:

```
{
  "version": "1.0.0",
  "generated_at": "2026-04-20T10:00:00Z",
  "model_used": "gpt-4o-mini",
  "prompt_template_id": "n5_grammar_v1",
  "validated_by": "tsukuya",
  "validated_at": "2026-04-20T15:00:00Z"
}
```

### 8-2. 변경 시점

청크 내용을 변경할 때:

1. `version` 마이너 (1.0.0 → 1.1.0)
2. `generated_at` 갱신
3. `embedding_text` 변경 시 재임베딩 (databaseSchema 13장)
4. `metadata.changelog` 배열에 변경 사유 추가 (선택)

### 8-3. 데이터셋 단위 버전

전체 N5/N4/N3 데이터셋의 큰 변경은 `decision_log.md`에 기록:

```
### [DATA] N5 청크 데이터셋 v2 적용

**결정:** N5 84개 청크 전체를 v2 프롬프트 템플릿으로 재생성한다.
**근거:** 츠쿠야 검수에서 'connection' 필드 일관성 이슈가 다수 발견됨.
**영향 범위:** 모든 N5 청크 재임베딩, 캐시 무효화.
```

---

## 9. 비용 관리 (LLM API 호출)

데이터 파이프라인에서 발생하는 OpenAI API 비용 관리 원칙입니다.

### 9-1. 비용 발생 지점

| 지점 | 모델 | 빈도 | 추정 |
|------|------|------|------|
| 청크 배치 생성 | gpt-4o-mini | 1회 (초기) + 변경 시 | N5 84개 ≈ $0.5~1 |
| 임베딩 생성 | text-embedding-3-small | 청크 변경 시 | N5 84개 ≈ $0.01 |
| LLM 응답 (학습 시) | gpt-4o-mini | 사용자별 | 캐시로 절감 |

### 9-2. 비용 절감 원칙

- **`llm_response_cache` 테이블 적극 활용** (`database_schema.md` 14장)
- **임베딩은 변경분만 재생성** (`embedding_text` 해시 비교)
- **배치 생성은 dry-run 후 본 실행** (프롬프트 검증)
- **품질 비교가 필요한 경우에만 GPT-4o**, 기본은 mini

### 9-3. 비용 모니터링

- 배치 호출 로그에 `token_usage` 기록 (`data/generated/_logs/`)
- 월별 사용량은 OpenAI dashboard에서 확인
- 예상 초과 시 민석에게 에스컬레이션

### 9-4. 비용 안전장치

- 배치 스크립트에 **최대 호출 수 제한** 환경변수 (`LLM_MAX_CALLS_PER_RUN`)
- 환경변수 미설정 시 **기본값 200건**
- 200건 초과 시 명시적 `--force` 플래그 요구

---

## 미결 및 상태 (임시)
> 단일 진실 = `project_summary.md` + `decision_log.md` + `glossary.md` + `planning/session_N/pm_minseok/summary.md`.

- **N5 84개 LLM 필드 생성**: 재현 배치 스크립트 대기 (가장 큰 병목)
- **N4/N3 기준표 작성**: N5 파이프라인 검증 후 진행 (담당: 수진)
- **`data/README.md` 작성**: 디렉토리 사용 규칙 명문화 (담당: 재현 또는 수진)
- **프롬프트 템플릿 ID 체계 확정**: `metadata.prompt_template_id` 명명 규칙 (담당: 재현)
- **재임베딩 트리거 자동화 여부**: 청크 변경 시 자동 vs 수동 (담당: 재현)
- **Tatoeba 예문 도입 여부**: 어색한 LLM 예문 발견 시점에 결정 (담당: 츠쿠야 + 수진)
- **JMdict 도입 시점**: Phase 2 어휘 영역 진입 시 (담당: 민석)x