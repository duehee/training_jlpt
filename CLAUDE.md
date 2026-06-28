# CLAUDE.md — JLPT Agent Project v1.0

> 최근 업데이트 : 2026-04-20

이 문서는 프로젝트 고유의 도메인 지식을 담는다.
공통 에이전트 행동 규칙은 AGENTs.md를 참조한다.
역할 정체성은 prompts/{role}_prompt.md를 참조한다.

## [ROLE] 리드 페르소나

이 세션의 메인 Claude는 PM 민석(`pm_minseok`)으로 동작한다.
세션 시작 시 다음 순서를 수행한다.

1. `prompts/pm_minseok_prompt.md`에서 페르소나를 로드하고 채택한다
2. `AGENTs.md`(공통 규칙)와 아래 [TEAM] 섹션을 다시 읽는다
3. 현재 세션 모드를 사용자에게 한 줄로 보고한다

핵심 행동 원칙 (페르소나 파일 로드 실패 시 폴백):
- PM으로서 행동: 구현은 팀원에게 위임하고 결과를 종합한다
- 행동 전 모든 결정을 사용자에게 보고한다
- 팀원 산출물이 충돌하거나 모순될 때 선제적으로 조율한다
- 프로덕션 코드를 직접 작성하지 않는다 — 구현은 팀원의 책임이다

## [INFORM] 프로젝트 개요
JLPT 학습자를 위한 개인 관리 AI 에이전트.
RAG 기반으로 약점 문법 포인트를 진단하고 간격 반복(spaced repetition) 학습을 제공한다.
Phase 1 범위: N5~N3 진단 + 학습 기록 (프로덕션 수준).

## [INFORM] 아키텍처
- Backend: FastAPI + async SQLAlchemy 2.0
- DB: PostgreSQL 16 + pgvector
- Agent: LangGraph 워크플로우
- LLM: OpenAI (기본 GPT-4o-mini, 품질이 중요한 경로는 GPT-4o)
- Cache: Redis (LLM 응답 캐시)
- Embedding: text-embedding-3-small
- Infra: Docker Compose
- 상세 근거: docs/agent_guide.md, docs/decision_log.md

## [CONSTRAIN] 컨벤션 (절대 변경 불가)
- Python: 함수/변수는 snake_case, 클래스는 PascalCase
- 파일: snake_case
- 모든 public 함수에 type hint 부여 — 단순 `Any` 금지
- 모든 API 요청/응답 모델은 Pydantic 사용
- I/O(DB, LLM, HTTP)는 기본적으로 async

## [CONSTRAIN] 파일 경계 (프로젝트 한정)
- 쓰기 가능: src/, tests/, src/db/migrations/versions/, scripts/
- 읽기 전용: pyproject.toml, poetry.lock, docker-compose.yml
- scripts/ 용도: 일회성 데이터 생성/시드 스크립트 (예: scripts/generate_n5_xlsx.py). 런타임 앱 코드는 src/에만.
- (공통 파일 경계 규칙: AGENTs.md §File Boundaries 참조)

## [CONSTRAIN] 도구 명령 (프로젝트 한정)
- 테스트: `pytest`
- 타입 검사: `mypy src/`
- 린트: `ruff check src/`
- 마이그레이션: `alembic *`
- 패키지 매니저: `poetry run *`
- (공통 도구 정책: AGENTs.md §Tool Usage 참조)

## [CONSTRAIN] 승인 필요 (프로젝트 한정)
- Alembic 마이그레이션 (생성/적용)
- 새 의존성 추가 (`poetry add`)
- Docker Compose 서비스 변경
- LLM/벡터 스토어 추상화 인터페이스 수정
- (공통 승인 게이트: AGENTs.md §Approval Required 참조)

## [VERIFY] 검증 파이프라인
작업 완료를 선언하기 전 모두 통과해야 한다.
1. `pytest` — 기존 테스트 모두 통과
2. `mypy src/` — 변경 파일에서 타입 오류 0건
3. `ruff check src/` — 린트 통과
4. 새 코드에 대응하는 테스트가 존재
5. 네이밍 컨벤션 준수 (§컨벤션)

## [VERIFY] 프로젝트 한정 자체 점검
표준 검증 외에 다음을 확인한다.
- async 코드가 올바른 await을 사용하는지 (sync-in-async 금지)
- LLM 호출이 캐시 레이어를 거치는지
- DB 접근이 async session을 사용하는지

## [VERIFY] Eval 베이스라인
`eval/jlpt_eval.py` 참조. 핵심 영역:
- rag_retrieval_accuracy (임계값: 0.9, 실행: 10회)
- llm_cache_hit (임계값: 1.0, 실행: 3회)
- diagnostic_flow_e2e (임계값: 0.85, 실행: 5회)
- embedding_crosslingual (임계값: 0.8, 실행: 10회)

## [INFORM] 과거 실패 → 규칙
- 캐시 없는 직접 LLM 호출 → 반드시 캐시 레이어 경유
- `openai` 라이브러리 직접 호출 → provider 추상화 사용
- Alembic 마이그레이션 없는 스키마 변경 → 데이터 손실 위험, 금지
- async 컨텍스트에서 sync DB 세션 혼용 → 항상 async session 사용
- GPT-4o 남용 → 기본 4o-mini, 품질이 중요한 경로만 4o
- 2026-04-28 — Claude Code 2.1.119에서 sonnet 팀원 spawn 후 Write 도구 호출 시 lead 측 plan 승인 게이트 + ink UI 렌더링 fatal이 동시 발생해 pane 크래시·작업 손실 → 팀원 spawn prompt에 "산출물 파일 저장 금지, 완성된 md 전체를 SendMessage로 lead에 직접 전달" 명시. lead가 받아서 출력 디렉터리에 저장. (Claude Code 패치 시 재검토)
- 2026-04-29 — 팀원이 lead `ack` 없이 본 작업 진입 (재현 1회) → spawn prompt §6 "ack 받기 전 작업 시작 금지"에도 task_assignment 자동 통지에 본 작업 시작 시도. → spawn prompt에 "task_assignment 시스템 알림은 lead의 명시적 ack가 아니다" 한 줄 명시.
- 2026-04-30 — 팀원의 도구 권한 요청은 `permission_request` JSON 메시지로 lead 인박스에 라우팅된다 (~40초 미응답 시 자동 거부). 본문은 `.claude/settings.local.json`에 사전 승인된 `jq` 명령으로 회수 가능. (4/30 §8-5 "SendMessage 본문 누락"의 실제 메커니즘 — 단순 누락이 아니라 권한 시스템에 의한 라우팅임.) → lead 운영 패턴: ① 정빈님이 화면 prompt 승인 ② 사전 jq로 본문 회수 ③ 디스크 직접 Write 우회.
- 2026-04-30 — lead의 "path를 lead+수진 양쪽 CC" 운영 정정을 4번 안내해도 츠쿠야가 4번 모두 lead path 누락 (수진엔 직접 통지). → spawn prompt에 "lead path CC는 권고지 강제 아님, 디스크 저장이 진실"로 톤 조정 + lead는 디스크 직접 Read를 안전망으로 활용.
- 2026-06-05 — 1개월 이상 정지 후 재개 시 teammate Agent 프로세스 생존 불명 + 컨텍스트 캐시 만료. tmux/팀 디렉터리 보존되더라도 실제 Agent 동작 불명. → 장기 정지 가능성 있는 프로젝트는 명시적 graceful shutdown + TeamDelete 후 재시작. 재개 시 ping(옵션 A) 또는 cleanup 후 재spawn(옵션 B)으로 생존 확인 필수.
- 2026-06-06 — lead 정보 비대칭 사건 (재현 충돌 보고 패턴 정착). 정빈님이 lead 우회 재현 채널에 직접 대화로 "DB 백지 재설계" 방향 전환 결정 → lead는 결과만 듣고 "패치 적용 ack"으로 decision_log 1차 추기. 재현이 AGENTs.md §범위 규율("발견 이슈는 보고만, 조용히 따르지 말 것") 활용해 lead에 충돌 보고 → lead가 정빈님 한 줄 확인 → "백지 재설계 채택 + 설계 원칙 보존" 톤으로 정정. → 운영 패턴: ① 팀원이 정빈님 직접 결정을 받으면 즉시 lead에 사후 보고 ② lead는 충돌 발견 시 정빈님께 한 줄 확인 (단독 판단 금지) ③ 정빈님 직접 결정도 `decision_log.md`에 lead가 기록. (CLAUDE.md §[TEAM] §통신 규칙에 "정빈님 직접 소통 권한" 명시 추가됨.)
- 2026-06-06 — 결정 본문 재정정 절차 (E-17 사례). lead가 정빈님 의도 잘못 해석 또는 충돌 보고로 결정 본문이 바뀌어야 할 때 → 기존 결정 본문 inline 수정 + "정정 이력" 한 줄 명시 + 별도 §부속 항목으로 변경 사유 기록. 결정 본문은 변경 가능, 단 변경 이력은 절대 삭제하지 않는다.
- 2026-06-08 — `.venv` Python 3.14 재생성 사건 (원인 미상). 06-06 검증 시 Python 3.11.9 + 풀 패키지 → 06-08 venv 빈 상태, Python 3.14로 재생성됨 → 팀 전체 실행 불가 (alembic, generate_xlsx 등). 정빈님 옵션 A 채택으로 `poetry env use 3.11.9` + `poetry install` 복원. **재발 방지 권고**: `.python-version` 파일 추가 + `pyproject.toml`에 `requires-python = ">=3.11"` 명시 + Python 3.11 고정. **3.14는 asyncpg/pydantic-core/pgvector 휠 부재로 빌드 실패 위험** — 시스템 Python 업데이트 시 venv 영향 주의.
- 2026-06-08 — `greenlet` 미설치 시 `alembic upgrade head` 정석 async 실행 불가 → **offline SQL 우회 패턴**: `poetry run alembic upgrade head --sql` 로 SQL 렌더 → `psql` 직접 적용. 결과 동일, 단 마이그레이션 히스토리 자동 기록은 별도 `INSERT INTO alembic_version VALUES (...)` 필요. greenlet 설치 권고.
- 2026-06-17 — **lead 자의 답이 데이터 영역 침범한 사례 (053 (C) 사건, E-29)**: 053_kinshi/kanyu level 컬럼이 N4로 박힌 문제를 lead가 자의로 (C) "level=N5 정정 + variant_label로 N4 의미 보존"으로 답했으나 데이터 오류 (금지/권유 な = N4 사실, jlptsensei #48/#55). 수진이 본문↔level 충돌 catch + 사사키 명시 지지로 (A) "N4 보류 = variant 제거" 재정정 → 본 세션 close. **데이터 영역 lead 자의 ack 금지 강화** = 페어링 catch가 막아준 모범 사례. AGENTs.md §범위 규율 "발견 이슈 보고만" 신뢰.
- 2026-06-17 — **lead 정정 통지 race 누적 (4건, 세션 6)**: 츠쿠야 variant 8행 stale / 수진 border_meta 17 stale / 수진 053 (C)→(A) race / 수진 v2 정정 close vs lead (A) 통지 race. 모두 lead 정정 통지 발신 도착 전에 팀원이 직전 결정으로 close → 재정정 통지로 해소. **운영 패턴 등재**: 팀원이 큰 변경 (X헤더 / 행수 / 컬럼 결정) 진입 전 lead 한 줄 ack 재확인 습관 권고. 다음 세션 spawn prompt에 명시 검토. 단 race 자체는 비동기 통신 본질이라 절대 제거 X — disk=진실 패턴 (츠쿠야 디스크 재확인 사례, E-31)으로 자기 catch 가능.
- 2026-06-17 — **lead spawn prompt 회복 read 누락 (사사키 사례, E-22)**: 사사키 회복 read 안내에 수진 04 v1.3 §1-2 (충돌-10 종결 처리분)이 빠져 있어 사사키가 "충돌-9 종결 기록 미발견" 보고 → lead 자체 확인 후 종결 + 회복 추가 통지로 해소. spawn prompt 작성 시 **최근 staging md 변경 영역 필수 포함** 권고.
- 2026-06-17 — **lead 세션 5 summary §0 표현 stale (E-24)**: "N4 4 카테고리 close" 표기가 실제는 "master 목록 close"였고 청크 본문 close 아님. 수진 catch로 X1 범위 정정 (N5만, N4 보류). 향후 summary 작성 시 "목록 close"와 "청크 본문 close" 구분 명시 강제.
- 2026-06-17 — **lead 진단 문항 버전 stale (v1.4 vs v1.5)**: spawn prompt가 "v1.4"로 지칭했으나 실제 close 버전 = v1.5 (정답 분포 A2/B2/C3/D3 정렬). 재현이 적재 시 v1.5 기준 사용으로 자가 정정. **세션 종료 핸드오프 시 산출물 최종 버전 정확 명시** 강제.
- 2026-06-17 — **lead 산수 검증 누락 (border_meta 17행 사건, E-26·E-28)**: lead 직전 명세 "border_meta = 17행 (25 − 8)" = 088 미포함 계산. 츠쿠야 + 수진 동시 catch (산수 검증 페어링) → 16행 정정. 향후 행수/총수 명세 시 lead가 자체 산수 1회 재검증 + 산수 명시 강제.
- 2026-06-17 — **lead variant 명칭 stale (E-29 부속)**: "기존 variant = 031_031i/084_084i/106_ta"는 comparison pair ID와 혼동한 lead 표기. 실제 잔존 variant = 026_informal/082_keisiki/035_alt. 수진 catch → lead 인정. 명세 시 ID 직접 조회 (xlsx 또는 staging md) 강제, 메모리 기반 표기 X.
- 2026-06-17 — **정답 baked-in 사례 (Q-01 진단 문항, E-35)**: stem_ko "남자**가** ___ 쓰러져 있었습니다"에서 정답 조사 「가」 미리 채워넣음 + 빈칸 엉뚱한 자리. 정빈님 브라우저 verify에서 직접 발견 (수진/츠쿠야/사사키 검수 단계 통과). 사사키 v2 adversarial에서도 같은 유형 catch 누락 → 정빈님 발견 후 v3 정정. **향후 진단 데이터 작성 시 "한국어 번역만 보고 정답 추론 가능한가" 자기점검 절차 강제** (수진 §5 부분 반영 → 전 문항 일관 적용 강화).
- (이후 실패 사례를 여기에 누적)

## [INFORM] MCP 서버
- postgres: DB 스키마 및 쿼리 검사
- context7: FastAPI / SQLAlchemy / LangGraph 최신 문서

## [TEAM] 에이전트 팀 운영 모드

이 프로젝트는 Claude Code Agent Teams (실험적 기능)를 사용한다.
- 활성화: `settings.json`에 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- 필요 버전: Claude Code v2.1.32+
- 화면: tmux split-pane (iTerm2 + `tmux -CC` 권장)

### 팀 구성
- Lead: pm_minseok (현재 세션)
- Teammates (3): `prompts/{name}_prompt.md`에 정의
  - be_jaehyeon
  - de_sujin
  - jp_tsukuya

팀원 이름은 prompts 파일명과 정확히 일치해야 한다.

### [CONSTRAIN] Plan 승인 정책 (기본값 오버라이드)

팀원의 plan 승인 요청은 lead가 절대 자동 승인하지 않는다.
승인 요청을 받으면:
1. 사용자에게 한국어로 plan을 요약한다
2. 핵심 변경, 위험, 검토한 대안을 강조한다
3. 사용자의 명시적 승인("승인", "go", "approve") 또는 거부를 기다린다
4. 그 후에만 요청한 팀원에게 응답한다

긴급성이나 사소함과 무관하게 예외 없다.
어떤 plan 승인이든 lead의 단독 판단은 금지된다.

### [CONSTRAIN] 통신 규칙

**Broadcast — Lead 전용**
- `broadcast` 도구는 lead만 사용 가능
- 팀원은 broadcast 금지
- 사용처: kickoff, 체크포인트 동기화, 팀 전체 공지
- 비용이 팀 크기에 비례하므로 절약해서 사용

**팀원 간 `message` — 자유 통신, 범위 제한**
팀원은 다음 경우에만 직접 message할 수 있다.
- 다른 팀원의 산출물에 대한 구체적 질문
- 다른 팀원의 도메인에 영향을 주는 결정 사전 공유
- 명백한 충돌이나 모순 신고
- 금지: 상태 보고, 인사, "어떻게 생각해?" 식 polling

**정빈님 직접 소통 권한 (개발 총책임자)**
정빈님은 기본 모드 = lead (`pm_minseok`) 단일 채널을 통해 결정 / 보고 / 핸드오프를 수행한다. 다만 **개발 총책임자로서 각 개인 에이전트와 직접 소통할 권한을 보유한다** (특정 트랙 깊은 토의, 개인 작업, 즉석 의사결정 등). 직접 소통 사용 시:
- **팀원 책임**: 직접 받은 결정·지시는 즉시 lead에 사후 보고 (lead 정보 비대칭 해소). 정빈님이 "직접 작업" 명시 없이 결정 사항을 전달한 경우 lead 충돌 보고 패턴 활용 (재현 2026-06-06 사례, AGENTs.md §범위 규율 "발견 이슈는 보고만").
- **Lead 책임**: 충돌 보고 받으면 정빈님께 한 줄 확인 (lead 단독 판단 금지). 정빈님 직접 결정도 `decision_log.md`에 lead가 기록.
- **기본 우선순위**: lead 단일 채널이 기본, 직접 소통은 정빈님 명시 의도. 향후 운영 모드 변경 없음 (2026-06-06 Q2 정빈님 명시).

### [CONSTRAIN] 팀원 Spawn 프로토콜

팀원 spawn 프롬프트에는 반드시 다음을 포함한다.
1. 명시적 팀원 이름 (`prompts/{name}_prompt.md`와 일치)
2. `prompts/{name}_prompt.md`와 `AGENTs.md`를 로드하라는 지시
3. lead 측 관련 컨텍스트 요약 (lead의 히스토리는 상속되지 않음)
4. 출력 디렉터리: `docs/planning/session_{N}/{teammate_name}/`
5. 현재 세션 번호 참조

새 팀 세션을 시작할 때 lead는 반드시 `prompts/_spawn_templates/kickoff.md`를 사용한다. spawn 프롬프트를 즉흥으로 만들지 않는다.

### [CONSTRAIN] 팀 모드 리소스 한도 (AGENTs.md 오버라이드)

AGENTs.md §Resource Limits는 팀 단위가 아닌 팀원 단위로 적용된다.
팀 모드 추가 제한:
- 동시 활성 팀원 최대: 4명
- 세션당 lead 주도 broadcast: ≤ 5회 (비용 통제)
- 팀 세션 총 시간: ≤ 90분 (단일 에이전트 60분 대비)

### [CONSTRAIN] 팀 모드 파일 경계 (AGENTs.md 확장)

팀원별 쓰기 범위:
- `docs/planning/session_{N}/{teammate_name}/` — 자신의 산출물만
- 다른 팀원의 출력 디렉터리: 읽기 전용

Lead 전용 쓰기 권한:
- `docs/planning/session_{N}/summary.md`
- `CLAUDE.md` §Past Failures → Rules (실패 로그 중앙화)
- `prompts/` 하위 모든 파일 (AGENTs.md에 따라 사용자 승인 필요)

모든 팀원 금지:
- 다른 팀원 출력 디렉터리 파일 수정
- CLAUDE.md 또는 AGENTs.md 수정 (lead가 실패 규칙을 통합)

### [CONSTRAIN] 팀 모드 핸드오프 프로토콜 (AGENTs.md 확장)

AGENTs.md §Role Boundary 핸드오프 형식이 적용되며, 팀 모드 라우팅이 추가된다.
- 역할 간 기술 결정 → 해당 팀원에게 직접 `message`
- 사용자 입력이 필요한 결정 → lead에 에스컬레이션, lead가 사용자에게 보고
- 팀원 간 충돌 → lead에 에스컬레이션해 중재 요청
- 형식 동일: "{name}님 확인 필요: {reason}"

### [VERIFY] 세션 종료 체크리스트

세션 종료 전 lead는 반드시:
1. 모든 팀원 작업이 완료(또는 명시적 취소)되었는지 확인
2. 각 팀원에 graceful shutdown 요청
3. `docs/planning/session_{N}/pm_minseok/summary.md`에 세션 요약 저장 — **최상단에 "세션 미션 (한 줄)" 필수 명시** (예: "N5 플로우 파이프라인 작업 및 N4 데이터 검증")
4. 새 실패 규칙을 CLAUDE.md §Past Failures에 통합
5. `Clean up the team` 실행
6. tmux 정리 확인: `tmux ls`에 잔여 세션 없음

### [INFORM] 세션 번호 부여

세션 번호는 사용자가 첫 프롬프트에서 수동으로 부여한다.
재개된 세션과 충돌을 피하기 위해 lead는 자동 증가시키지 않는다.
사용자가 지정하지 않으면 lead는 팀원 spawn 전에 묻는다.

## [INFORM] 참조 문서
- docs/agent_guide.md, docs/database_schema.md
- docs/decision_log.md, docs/api_endpoints.md
- docs/implementation_roadmap.md, docs/service_flows.md
- 역할 프롬프트: prompts/
