# 에이전트 운영 가이드

> 최종 업데이트: 2026-04-14
> 이 문서는 이 저장소에서 에이전트가 어떻게 협업해야 하는지 정의합니다.

---

## 1. 기준 문서 우선순위

정보가 충돌할 때는 아래 순서로 판단합니다.

1. `/projectState.json`
2. `/docs/decisionLog.md`
3. `/docs/developmentBlueprint.md`
4. `/docs/apiEndpoints.md`, `/docs/serviceFlows.md`, `/docs/productOverview.md`
5. `/docs/localDevSetup.md`
6. `/CLAUDE.md`

`projectState.json`은 현재 작업 상태의 기준입니다.
`decisionLog.md`는 확정된 의사결정의 기준입니다.

---

## 2. 저장소 구조

```text
training_jlpt/
├── projectState.json              공유 상태 파일
├── CLAUDE.md                      재현 에이전트 페르소나 및 기술 가드레일
├── docs/
│   ├── agentGuide.md              에이전트 운영 가이드
│   ├── productOverview.md         제품 배경과 사용자 문제
│   ├── serviceFlows.md            서비스 플로우와 Phase 범위
│   ├── developmentBlueprint.md    개발 골격 초안
│   ├── apiEndpoints.md            API 계약 초안
│   ├── decisionLog.md             확정 의사결정 기록
│   ├── localDevSetup.md           로컬 개발 환경 가이드
│   ├── newUserOnboardingFlow.svg
│   └── coreLearningAgentFlow.svg
├── data/                          데이터 산출물
├── src/                           애플리케이션 코드
├── docker-compose.yml
└── pyproject.toml
```

---

## 3. 문서 역할 분리

| 문서 | 역할 | 갱신 기준 |
|------|------|----------|
| `projectState.json` | 현재 상태, 담당자, 핸드오프, 이슈 | 작업 상태가 변할 때 |
| `decisionLog.md` | 확정된 결정과 근거 | 결정이 확정될 때 |
| `developmentBlueprint.md` | 전체 개발 순서와 골격 | 구현 방향이 바뀔 때 |
| `productOverview.md` | 제품 배경과 문제 정의 | 제품 방향이 바뀔 때 |
| `serviceFlows.md` | 사용자 흐름과 Phase 범위 | 플로우가 바뀔 때 |
| `apiEndpoints.md` | 구현용 API 경계 | 백엔드 설계가 바뀔 때 |
| `localDevSetup.md` | 로컬 환경 재현 방법 | 인프라나 도구가 바뀔 때 |

개요 문서에 임시 작업 상태를 적지 않습니다.
상태성 정보는 반드시 `projectState.json`에 둡니다.

---

## 4. 기본 작업 흐름

### 시작할 때

1. `/projectState.json` 읽기
2. 자신의 `agents.{id}` 블록 확인
3. `handoffQueue`, `openIssues`, `deliverables` 확인
4. 현재 작업에 필요한 문서만 읽기

### 끝낼 때

최소한 아래를 갱신합니다.

- `agents.{id}.status`
- `agents.{id}.currentTask`
- `agents.{id}.nextAction`
- `meta.lastUpdated`

필요 시 함께 갱신합니다.

- `handoffQueue`
- `openIssues`
- `deliverables`
- `decisionLog`

---

## 5. 역할 경계

| 에이전트 | 주 역할 | 주로 갱신하는 항목 |
|---------|--------|-------------------|
| `minseok` | 우선순위, 승인, 범위 확정 | `projectState.json`, 승인 관련 항목 |
| `sujin` | 문법 데이터 작성 | `projectState.json`, 데이터 산출물 |
| `tsukuya` | 생성물 검수와 품질 확인 | `projectState.json`, 검수 관련 기록 |
| `jaehyeon` | 백엔드, 인프라, RAG, 워크플로우 | `projectState.json`, 기술 문서, 구현물 |

생성과 검수는 같은 에이전트가 맡지 않습니다.

---

## 6. 실행 예시

```bash
claude --system-prompt prompts/수진_에이전트_프롬프트.md \
  "projectState.json을 읽고 현재 작업 상태를 확인한 뒤 작업을 이어가. 완료 후 projectState.json을 업데이트해."
```

```bash
claude --system-prompt prompts/재현_에이전트_프롬프트.md \
  "projectState.json을 읽고 nextAction 기준으로 작업 시작. 완료 후 projectState.json과 관련 문서를 업데이트해."
```

---

## 7. 네이밍 원칙

- 문서 파일명은 `camelCase`를 유지합니다.
- 문서 본문은 한글 작성이 기본입니다.
- 상태 파일 이름은 `projectState.json`으로 고정합니다.
- 다이어그램 파일도 동일한 네이밍 규칙을 따릅니다.
