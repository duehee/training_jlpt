# 에이전트 운영 가이드

> 최종 업데이트: 2026-04-19
> 담당 축: **Who** — 누가 무엇을 담당하는가
> 관련 문서: `product_overview.md`, `decision_log.md`, `implementation_roadmap.md`

---

## 📌 빠른 참조 (에이전트용)

**이 문서에서 찾을 수 있는 것**
- 기준 문서 우선순위 → 1장
- 저장소 구조 → 2장
- 문서 역할 분리 표 → 3장
- 기본 작업 흐름 (시작/끝) → 4장
- 에이전트별 역할 경계 → 5장
- 실행 예시 (claude CLI) → 6장
- 네이밍 원칙 → 7장

**이 문서에서 찾을 수 없는 것**
- 제품 맥락 → `product_overview.md`
- 확정된 결정 → `decision_log.md`
- 구현 순서 → `implementation_roadmap.md`
- 각 역할별 상세 프롬프트 → `prompts/*_prompt.md`

---

## 이 문서는
이 저장소에서 **에이전트들이 어떻게 협업**해야 하는지를 정의합니다.
역할 분리, 문서 우선순위, 핸드오프 규칙의 단일 진실 원천입니다.

---

## 1. 기준 문서 우선순위

정보가 충돌할 때는 아래 순서로 판단합니다.

1. `projectState.json` (예정) — 현재 작업 상태
2. `docs/decision_log.md` — 확정된 의사결정
3. `docs/implementation_roadmap.md` — 구현 순서
4. `docs/database_schema.md`, `docs/api_endpoints.md` — 기술 계약
5. `docs/service_flows.md`, `docs/product_overview.md` — 제품 맥락
6. `docs/local_dev_setup.md` — 로컬 환경
7. `CLAUDE.md` — 전역 코딩 규칙

`projectState.json`은 **현재 작업 상태**의 기준입니다.
`decision_log.md`는 **확정 의사결정**의 기준입니다.

---

## 2. 저장소 구조

```
training_jlpt/
├── projectState.json              공유 상태 파일 (예정)
├── CLAUDE.md                      전역 코딩 규칙 / 재현 페르소나 가드레일
├── docs/
│   ├── agent_guide.md              에이전트 운영 가이드 (이 문서)
│   ├── product_overview.md         제품 배경과 사용자 문제
│   ├── service_flows.md            서비스 플로우와 Phase 범위
│   ├── implementation_roadmap.md   구현 순서와 Stage 상세
│   ├── database_schema.md          DB 스키마
│   ├── api_endpoints.md            API 계약
│   ├── decision_log.md             확정 의사결정 기록
│   ├── local_dev_setup.md           로컬 개발 환경 가이드
│   ├── new_user_onboarding_flow.svg
│   └── core_learning_agent_flow.svg
├── prompts/
│   ├── AGENTs.md                  공통 하네스 규칙
│   ├── be_jaehyeon_prompt.md      재현 (AI + 백엔드 + 인프라)
│   ├── de_sujin_prompt.md         수진 (데이터)
│   ├── jp_tsukuya_prompt.md       츠쿠야 (검증)
│   └── pm_minseok_prompt.md       민석 (PM)
├── data/                          데이터 산출물
├── src/                           애플리케이션 코드
├── tests/                         테스트
├── docker-compose.yml
└── pyproject.toml
```

---

## 3. 문서 역할 분리

| 문서 | 담당 축 | 갱신 기준 |
|------|---------|----------|
| `projectState.json` (예정) | 현재 상태 | 작업 상태가 변할 때 |
| `decision_log.md` | 확정 결정 | 결정이 확정될 때 (삭제 없음) |
| `implementation_roadmap.md` | 구현 순서 | Stage 범위가 바뀔 때 |
| `product_overview.md` | 제품 배경 | 제품 방향이 바뀔 때 |
| `service_flows.md` | 사용자 흐름 | 플로우가 바뀔 때 |
| `database_schema.md` | DB 스키마 | 스키마가 바뀔 때 |
| `api_endpoints.md` | API 계약 | 엔드포인트가 바뀔 때 |
| `local_dev_setup.md` | 로컬 환경 | 인프라/도구가 바뀔 때 |

### 핵심 원칙

- **한 사실은 한 문서에만** (SSOT: Single Source of Truth).
- 개요 문서에 임시 작업 상태를 적지 않습니다.
- 상태성 정보는 `projectState.json`에 둡니다 (예정).
- 번복되는 결정은 `decision_log.md`에 **새 항목**으로 추가하고 기존 항목은 삭제하지 않습니다.

---

## 4. 기본 작업 흐름

### 4-1. 시작할 때

1. `projectState.json` 읽기 (예정)
2. 자신의 `agents.{id}` 블록 확인
3. `handoffQueue`, `openIssues`, `deliverables` 확인
4. 현재 작업에 필요한 문서만 선별적으로 읽기 (각 문서의 빠른 참조 섹션 활용)

### 4-2. 끝낼 때

최소한 아래를 갱신합니다 (예정).

- `agents.{id}.status`
- `agents.{id}.currentTask`
- `agents.{id}.nextAction`
- `meta.lastUpdated`

필요 시 함께 갱신합니다.

- `handoffQueue`
- `openIssues`
- `deliverables`
- `decision_log.md`

### 4-3. 핸드오프 시

`implementation_roadmap.md` 10장 "핸드오프 산출물 표준"을 따릅니다.

**파일 기반 산출물이 없으면 핸드오프는 완료되지 않은 것으로 간주합니다.**

---

## 5. 역할 경계

| 에이전트 | 주 역할 | 주로 갱신하는 항목 |
|---------|--------|-------------------|
| `minseok` | 우선순위, 승인, 범위 확정 | `decision_log.md`, `projectState.json` 의 승인 항목 |
| `sujin` | 문법 데이터 작성 | `data/curated/`, `projectState.json` |
| `tsukuya` | 생성물 검수와 품질 확인 | `docs/validation_checklist.md`, 검수 기록 |
| `jaehyeon` | 백엔드, 인프라, RAG, 워크플로우 | `src/`, `alembic/`, 기술 문서, `projectState.json` |

### 핵심 규칙

- **생성과 검수는 같은 에이전트가 맡지 않는다** (결정: 2026-04-10).
- **범위 변경이나 레벨 배정 판단 불확실 → 민석에게 에스컬레이션**.
- **기술 결정 → 재현 주도**, **제품 결정 → 민석 주도**.

### 향후 투입 예정 (Phase 2~3):**
- UX/UI 에이전트 (Phase 2 UI 고도화 시점)
- QA 에이전트 (Phase 3 품질 안정화 시점)
- 프론트엔드 에이전트 (Phase 3 대시보드 구축 시점)

---

## 6. 실행 예시

```
claude --system-prompt prompts/de_sujin_prompt.md \
  "projectState.json을 읽고 현재 작업 상태를 확인한 뒤 작업을 이어가. 완료 후 projectState.json을 업데이트해."
```

```
claude --system-prompt prompts/be_jaehyeon_prompt.md \
  "projectState.json을 읽고 nextAction 기준으로 작업 시작. 완료 후 projectState.json과 관련 문서를 업데이트해."
```

---

## 7. 네이밍 원칙

### 7-1. 파일명

| 위치 | 규칙 |
|------|------|
| `docs/` 하위 문서 | `snake_case.md` (예: `service_flows.md`) |
| `src/` 하위 코드 | `snake_case.py` (파이썬 관례) |
| `data/curated/` 산출물 | `snake_case.json` (예: `n5_grammar_chunks.json`) |
| 다이어그램 | `snake_case.svg` |
| 상태 파일 | `projectState.json` (고정) |

### 7-2. 문서 본문

- 한글 작성이 기본.
- 전문 용어는 영어 그대로 사용 (RAG, LLM, pgvector 등).
- 코드 식별자는 백틱(`` ` ``)으로 감싸기.

### 7-3. Git 커밋 메시지

- 한글 또는 영어 모두 허용.
- 관련 에이전트 이니셜 prefix 권장 (예: `[BE] ...`, `[DATA] ...`).

---

## 미결 및 상태 (임시)
> 향후 `projectState.json`으로 이전 예정

- **`projectState.json` 스키마 확정**: 구조 정의 후 초기 파일 생성 (담당: 민석 + 재현)
- **`docs/validation_checklist.md` 작성**: 츠쿠야 검수 체크리스트 별도 파일화 (담당: 츠쿠야)
- **prompts 재작성**: docs 안정화 후 prompts에서 중복 내용 제거 (향후 별도 작업)