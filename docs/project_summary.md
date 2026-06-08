# JLPT Agent Project — 전체 상황 요약

> 최근 갱신: 2026-06-06 (세션 4 N5 안정화 완료 시점)
> 단일 진실 위치: 본 문서 (개요) + `decision_log.md` (결정 누적) + `glossary.md` (용어) + `docs/planning/session_N/pm_minseok/summary.md` (세션별)
> 갱신 책임: lead (`pm_minseok`) — 세션 마무리 시 evolve

---

## §0. 한 페이지 (TL;DR)

| 영역 | 상태 | 진행 단계 |
|---|---|---|
| **Phase** | Phase 1 진행 중 | N5~N3 진단 + 학습 기록 (프로덕션 수준) |
| **N5 데이터** | ✅ **안정화 완료** (2026-06-06) | 109 base + 3 variant + 25 비교쌍 + BORDER 25 |
| **N4 데이터** | 미진입 | N5 안정화 후 Phase 1 잔여 트랙 |
| **N3 데이터** | 미진입 | 동상 |
| **트랙 1 (DB 스키마)** | 🔄 **백지 재설계 진입 대기** | 패치 폐기 (정빈님 직접 ack), N1~N5 공통 + xlsx 고정 입력 + 어댑터 분리 |
| **트랙 3 (적재 스크립트)** | 미진입 | 백지 재설계 확정 후 |
| **인프라 (Stage 0)** | 준비됨 | Docker / FastAPI / Alembic α baseline 골격 완비, `poetry add alembic` 미실행 |
| **인프라 (Stage 1+)** | 미진입 | 스키마 적재 / RAG 파이프라인 / 진단 워크플로우 |

**현재 가장 중요한 결정**: 트랙 1 DB 백지 재설계 (정빈님 2026-06-06 직접 결정). xlsx = 고정 입력 계약, 어댑터가 정규화 흡수, DB는 청결한 새 모델, N1~N5 공통 스키마.

---

## §1. 프로젝트 정체성

### 1-1. 목적
JLPT 학습자를 위한 **개인 관리 AI 에이전트**. RAG 기반 약점 문법 진단 + 간격 반복 학습.

### 1-2. Phase 1 범위
N5~N3 진단 + 학습 기록 (프로덕션 수준). N2/N1은 Phase 2+ 범위.

### 1-3. 정빈님 정체성
- 1인 개발자, 개발 총책임자
- AI 백엔드 엔지니어 취직 포트폴리오 + 상품성 있는 서비스
- 페르소나 채택: 민석(PM/PO) + 수진(데이터) + 츠쿠야(QA/일본어 native 검수) + 재현(Senior Backend / AI Engineer)

### 1-4. 사용자 ↔ AI 협업 모델
- 기본 모드: 정빈님 ↔ lead(`pm_minseok`) 단일 채널
- 개발 총책임자 권한: 정빈님은 각 개인 에이전트와 직접 소통도 가능 (2026-06-06 정빈님 명시, CLAUDE.md §[TEAM] 통신 규칙 반영)

---

## §2. 아키텍처 종합

### 2-1. 기술 스택 확정
- **Backend**: FastAPI + async SQLAlchemy 2.0
- **DB**: PostgreSQL 16 + pgvector (0.4.2 설치 완료)
- **Agent**: LangGraph 워크플로우
- **LLM**: OpenAI (기본 GPT-4o-mini, 품질 경로는 GPT-4o)
- **Cache**: Redis (LLM 응답 캐시)
- **Embedding**: text-embedding-3-small
- **Infra**: Docker Compose
- **xlsx 운영**: openpyxl (3.1.5 설치 완료)

### 2-2. 데이터 흐름 (현재 패치 방식 — 백지 재설계 진입 직전 모습)
```
[운영 진실 = xlsx]
  data/n5/n5_master.xlsx (5 시트)
  data/n5/n5_comparison.xlsx (2 시트)
    ↓ (어댑터 / 로더)
[DB (백지 재설계 target)]
  PostgreSQL 16 + pgvector
    ↓
[RAG 진단]
  text-embedding-3-small + chunks (point/compare/variant 통합)
    ↓
[학습 워크플로우]
  LangGraph + 간격 반복
```

### 2-3. 백지 재설계 원칙 (정빈님 2026-06-06 결정)
1. `level` 1급 차원 — N1~N5 공통 스키마, 레벨 하드코딩 0
2. xlsx = 고정 입력 계약 / 어댑터 = 정규화 단일 책임 / DB = 청결
3. 단일 진실 + 파생 뷰 — 양방향 수동 동기화 금지 (수동 동기 = 드리프트 원인, 츠쿠야 F1·F2 인풋)

### 2-4. 설계 원칙 보존 (D-1 ~ D-10, 재현 워크숍 plan에서 도출, 패치 폐기 후에도 유효)
| ID | 원칙 |
|---|---|
| D-1 | `chunk_type` enum = `point` / `compare` / `variant` 3종 (VARCHAR + 앱 Literal) |
| D-2 | variant → 단일 테이블 흡수 + `variant_of` (별도 테이블 X) |
| D-3 | comparison 2시트 → 단일 테이블 흡수 (메타 JSONB) |
| D-4 | `border_meta JSONB` + `l3_tags JSONB` 양쪽 신설 (RAG 필터 강건) |
| D-5 | 자기 대조 3쌍 (031_031i / 084_084i / 106_ta) — `left==right` 허용, `left!=right` CHECK 금지 |
| D-6 | 진단 문제 별도 테이블 (`diagnostic_questions` 또는 재설계 후 이름) |
| D-7 | `embedding_text` 길이 = point 150~270 / variant 120~150 / compare 50~100. DB CHECK 금지 |
| D-8 | `grammar_point_id` 참조 규약 = base point only |
| D-9 | `source_pool` JSON 통일 (배열 표기 일관, 어댑터 계약) |
| D-10 | variant `border_candidate` BOOLEAN NULL 허용 (미평가=NULL, 단 N5에서는 variant 전부 FALSE로 확정되어 D-10 자연 소멸 가능성 — 백지 target에서 재판단) |

---

## §3. N5 데이터 — 안정화 완료 (2026-06-06)

### 3-1. 최종 카운팅
| 항목 | 값 | 근거 |
|---|---|---|
| 마스터 base | **109** (IDs 001~110, 061 gap) | E-1 (-1) + E-12 (+5) |
| variant | 3건 (`_informal` / `_keisiki` / `_alt`) | E-7, E-11 |
| 비교쌍 | **25쌍** (Cluster A~F, 자기 대조 3쌍 포함) | E-5/E-10 (-2) + E-16 (+3) |
| BORDER 유효 | **25개** (base 21 + E-12 4건: 106·107·108·110) | 츠쿠야 §7 판정 |
| variant BORDER | 전부 FALSE | 츠쿠야 §6 판정 |
| L1 분류 | 9 그룹 (15+15+27+5+7+10+8+6+16=109) | E-2, E-12 |

### 3-2. 운영 데이터 위치
- `data/n5/n5_master.xlsx` (5 시트: master_list / taxonomy_def / l3_assignment / border_meta / variant_chunks)
- `data/n5/n5_comparison.xlsx` (2 시트: comparison_pairs / comparison_chunks)
- `data/schema/n5_master_schema.md` + `data/schema/n5_comparison_schema.md`

### 3-3. 검수 자료 (단일 진실 보조)
- 수진 v2 작성: `docs/planning/session_4/de_sujin/01~06_*.md` + `generate_n5_xlsx.py` (결정적 재생성 스크립트)
- 츠쿠야 v2 재검수: `docs/planning/session_4/jp_tsukuya/01_n5_v2_review.md` (조건부 승인) + `02_n5_v2_spot_check.md` (✅ 5/5 통과)

### 3-4. 한자/한글 정책 적용
- L1/L2 분류명 + 메타 표현 한자 → 한글화 (활용·문형·표현 등)
- 일본어 문법 형태·예문 한자 → 유지 (辞書形·た形·は·が 등, 학습 정확성)

---

## §4. 트랙별 진행 상태

### 4-1. 트랙 2 — 데이터 (수진 + 츠쿠야)
- **N5**: ✅ 안정화 완료 (2026-06-06)
- **N4**: 미진입 — 백지 재설계 + 어댑터 계약 안에서 별도 사이클로
- **N3**: 미진입 — 동상

### 4-2. 트랙 1 — DB 스키마 (재현)
- **세션 2**: Stage 0 골격 (Docker / FastAPI / Alembic α baseline / L3 운영 이슈) 완료
- **세션 4**: readiness 분석 (`01_readiness_check.md`) + 워크숍 plan (`02_workshop_plan.md`, **강등** — "왜 패치로는 안 되는지" 입력 자료)
- **백지 재설계 진입 대기**: `03_redesign_*.md` 백지 설계 2장 (도메인 플로우 + target DB 모델, 레벨 일반화 + 어댑터 경계) — 정빈님 + lead 함께 검토 게이트
- **사전 골격 메모** (재현 자율 정리): 원칙 3건 + 논점 4건 (chunk 통합 / border 속성화 / comparison 트리거→청크 도출 / 어댑터 정규화 계약)

### 4-3. 트랙 3 — 적재 스크립트 + RAG 파이프라인
- 미진입 — 백지 재설계 확정 후 진입
- 청크 100건+ 적재 시점 = base 109 + compare 25 + variant 3 = **137건** → 벡터 인덱스 IVFFlat 임계 충족 예정

### 4-4. 트랙 4 — 진단 워크플로우 + 학습 기록
- 미진입 — Stage 1+ 범위

---

## §5. 세션별 진행 누적

### Session 1 (~2026-04-28)
- 페르소나 + 데이터 형식 + 콘텐츠 형식 검토
- 산출물: 답변 (정빈님) + 4 통합 검토 (수진/재현/츠쿠야) + lead summary

### Session 2 (~2026-04-30)
- N5 마스터 105 + L1/L2 분류 + L3 태그 + chunk samples + 비교쌍 24
- Stage 0 골격 (Docker / FastAPI / Alembic / L3 운영 이슈)
- 산출물: 14건 + INDEX + xlsx v2 + 정빈님 답변 + lead summary
- 결정: E-1 ~ E-4 (BORDER 23→21 등 운영 정정)

### Session 3 (2026-04-30 ~ 2026-06-06, 1개월 정지 포함)
- 츠쿠야 N5 105 항목 6 검수 산출물 + opus 4.7 사전 검수 1건
- 정빈님 결정 11건 일괄 응답 (E-5~E-13, Q5, Q6)
- 산출물: 츠쿠야 7건 + lead `glossary.md` 신규 작성 + summary
- 1개월 정지 회복 패턴 정착

### Session 4 (2026-06-06)
- **트랙 2 마무리**: 수진 v2 (109/3/25) → 츠쿠야 재검수 (조건부 승인) → 후속 일괄 정정 → spot check (5/5 통과) → ✅ N5 안정화 완료
- **트랙 1 전환**: 재현 readiness + 워크숍 plan → 정빈님 직접 ack로 **패치 폐기 → 백지 재설계 채택**
- **결정 7건 추가**: E-14 (changelog 형식) / E-15 (variant BORDER 형식) / E-16 (비교쌍 +3 = 25쌍) / E-17 (백지 재설계 + 설계 원칙 보존 + Q2 통신 모드 정정)
- 운영 정정: lead 정보 비대칭 → 충돌 보고 패턴 정착 (재현 사례) / 결정 본문 재정정 절차
- 산출물: 수진 9건 + 츠쿠야 2건 + 재현 2건 + lead session4_status.md + decision_log E-14~E-17

---

## §6. 결정 누적 (decision_log.md 진실)

### E-시리즈 (정빈님 결정 누적)
| ID | 도메인 | 한 줄 |
|---|---|---|
| E-1 | DATA | grammar_n5_061 「か」 이중 등재 → 제거 |
| E-2 | DATA | grammar_n5_079/080 → L1-9 부사류 재분류 |
| E-3 | DATA | BORDER 총수 23 (lead 정정) |
| E-4 | DATA | decision_log L1 9그룹 갱신 |
| E-5 | DATA | 비교쌍 #18 (3-way) 제거 → 23쌍 |
| E-6 | DATA | 비교쌍 #20 (予定) 처리 — 보류 + 본문 메타 |
| E-7 | DATA | 이형태 서픽스 방식 (`_informal` 등) |
| E-8 | DATA | だけ/しか, から/ので → ★★★ 승급 |
| E-9 | DATA | comparison_pair = 비교 청크 생성 트리거 |
| E-10 | DATA | E-6 적용 후 비교쌍 = 22쌍 (해석 A, 이후 E-16 +3으로 최종 25쌍) |
| E-11 | DATA | variant → 별도 시트 `variant_chunks` |
| E-12 | DATA | 마스터 105 → 109 (5건 추가, 정정 후) |
| E-13 | PROCESS | xlsx 분리 = `n5_master.xlsx` (5시트) + `n5_comparison.xlsx` (2시트) |
| E-14 | PROCESS | 츠쿠야 재검수 changelog 형식 (옵션 A) |
| E-15 | PROCESS | variant BORDER 재평가 형식 (옵션 a 통합) |
| E-16 | DATA | 비교쌍 +3 → **25쌍** (Cluster F 신설), `compare_n5_106_ta` 수진 권한 위임 |
| E-17 | ARCH | **백지 재설계 채택** + 설계 원칙 10건 보존 + xlsx 고정 입력 + N1~N5 일반화 |

### D-시리즈 (재현 워크숍 plan 도출, §2-4 참조)
- D-1 ~ D-10 모두 백지 재설계 target의 설계 원칙으로 보존 (패치 적용은 폐기)

### Q-시리즈 (운영 / 인프라)
| ID | 한 줄 |
|---|---|
| Q5 | openpyxl 의존성 추가 승인 (3.1.5 설치) |
| Q6 | point embedding_text 길이 150~270자 정식 채택 |

---

## §7. 팀 + 페르소나 (Agent Teams 모드)

### 팀 구성
| 이름 | 역할 | 페르소나 파일 | 권장 모델 |
|---|---|---|---|
| `pm_minseok` (민석) | PM/PO Lead | `prompts/pm_minseok_prompt.md` | opus 4.7 |
| `de_sujin` (수진) | Data Engineer | `prompts/de_sujin_prompt.md` | sonnet |
| `jp_tsukuya` (츠쿠야) | QA Lead / 일본어 native 검수 | `prompts/jp_tsukuya_prompt.md` | opus 4.7 (정밀도 우선) |
| `be_jaehyeon` (재현) | Senior Backend / AI Engineer (RAG / FastAPI / Alembic / Docker) | `prompts/be_jaehyeon_prompt.md` | opus (Session 4 = 4.8 명시) |

### 운영 규칙
- Lead 단일 채널 (정빈님 ↔ lead) — 기본 모드
- 정빈님 직접 소통 권한 보유 (개발 총책임자, 2026-06-06 명시)
- 팀원 간 message 자유 통신 (범위 제한)
- broadcast = lead 전용
- 동시 활성 팀원 ≤ 4명
- 세션당 lead 주도 broadcast ≤ 5회

---

## §8. 운영 패턴 + 실패 규칙 (CLAUDE.md §과거 실패)

### 정착된 운영 패턴
- **권한 prompt 회수**: `.claude/settings.local.json` 사전 jq 명령 (~40초 timeout 자동 거부 우회)
- **teammate ↔ teammate 직접 대화**: lead 사후 보고 (data ↔ QA 자율 협업)
- **디스크 직접 저장 + path 통지**: SendMessage 본문 누락 회피 (lead 디스크 직접 Read 안전망)
- **lead 정보 비대칭 → 충돌 보고 패턴** (2026-06-06 재현 사례): 정빈님이 lead 우회 팀원 채널 직접 대화 시, 팀원이 AGENTs.md §범위 규율 활용해 lead에 충돌 보고 → lead가 정빈님 한 줄 확인 → 정정 흐름

### CLAUDE.md §과거 실패 통합 누적 (2026-04-28 ~ 2026-06-06)
- sonnet teammate Write + plan 승인 동시 발생 시 ink crash → SendMessage 본문 / 디스크 직접
- `task_assignment` 알림 ≠ lead 명시적 ack
- 권한 요청 = `permission_request` JSON으로 lead 인박스 라우팅 (~40초 timeout)
- lead path CC 강제력 한계 → 디스크 저장이 진실
- 1개월+ 정지 후 Agent 생존 불명 → 명시적 graceful shutdown + 재spawn
- tmux -CC 미진입 시 split-pane 분할 실패 → 반드시 `tmux -CC new`
- (본 세션 통합 대기) lead 정보 비대칭 충돌 보고 패턴 / 결정 본문 재정정 사례

---

## §9. 다음 단계 (Phase 1 잔여)

### 즉시 진입 가능 (현재 세션 내 또는 직후)
1. **재현 백지 재설계** `03_redesign_*.md` (정빈님 별도 ack 후) — 도메인 플로우 + target DB 모델, 정빈님 + lead 함께 검토
2. **glossary §9 connection_type** lead 자율 갱신 (재설계 영향 적음)
3. **git commit 사이클** (정빈님 별도 ack 필수, lead 자동 처리 금지)

### 후속 세션 진입 후보
4. **트랙 3 적재 스크립트** — 백지 재설계 확정 → xlsx → DB 어댑터 구현
5. **N4 데이터** — 어댑터 계약 정착 후 N4 수집·검수 (수진 + 츠쿠야)
6. **N3 데이터** — N4 진행 후
7. **Stage 1 인프라** — 스키마 적재 + RAG 파이프라인 + 진단 워크플로우 (재현)

### Phase 2 후보 (현 Phase 1 범위 외)
- N2 / N1 데이터 (N5~N3 안정화 + 적재 검증 후)
- BM 모델 결정 (정빈님 영역)
- 배포 방식 (PWA vs 네이티브)

---

## §10. 참조 문서 맵

### 의사결정 / 운영
- `decision_log.md` — 결정 누적 (E + D + Q 시리즈)
- `glossary.md` — 약어 + ID 패턴 + 운영 용어 (16 섹션)
- `CLAUDE.md` — 프로젝트 도메인 + 팀 운영 규칙 + 과거 실패
- `AGENTs.md` — 공통 에이전트 행동 규칙

### 기술 구조
- `database_schema.md` — DB 스키마 (백지 재설계 진입으로 일부 stale 가능성)
- `api_endpoints.md` — API 엔드포인트
- `service_flows.md` — 사용자 / 서비스 흐름
- `implementation_roadmap.md` — 구현 순서 (Stage 0 / Stage 1+)
- `data_pipeline.md` — 데이터 파이프라인
- `local_dev_setup.md` — 로컬 개발 환경

### 운영 데이터
- `data/n5/n5_master.xlsx` + `data/n5/n5_comparison.xlsx` — N5 운영 진실
- `data/schema/n5_*_schema.md` — xlsx 컬럼 명세

### 세션별 산출물
- `docs/planning/session_1/` ~ `session_4/` — 세션별 산출물 + summary

### 페르소나
- `prompts/pm_minseok_prompt.md` / `de_sujin_prompt.md` / `jp_tsukuya_prompt.md` / `be_jaehyeon_prompt.md`
- `prompts/_spawn_templates/kickoff.md` — 팀 세션 시작 템플릿

### 설계 문서 (제품 비전)
- `product_overview.md` — 제품 개요 + 페인포인트
- `agent_guide.md` — 에이전트 협업 가이드

---

## §11. 운영 진실 단일 출처 정리 (lead 갱신 책임)

| 단일 진실 | 위치 | 갱신 책임 |
|---|---|---|
| 결정 | `decision_log.md` | lead (정빈님 결정 도착 시 즉시) |
| 운영 용어 | `glossary.md` | lead (운영 정정 도착 시) |
| 세션 운영 | `docs/planning/session_N/pm_minseok/summary.md` | lead (세션 종료 시) |
| 프로젝트 전체 | **본 문서** `docs/project_summary.md` | lead (세션 종료 시 evolve) |
| 운영 데이터 | `data/{level}/*.xlsx` | 수진 (어댑터 도입 후 결정적 재생성) |
| 데이터 명세 | `data/schema/*.md` | 수진 |
| 페르소나 | `prompts/{name}_prompt.md` | 정빈님 (lead 단독 수정 금지) |
| 도메인 / 팀 규칙 | `CLAUDE.md` | 정빈님 ack 후 lead 갱신 |
| 공통 규칙 | `AGENTs.md` | 정빈님 ack 후 lead 갱신 |

기존 `projectState.json`은 stale 누적 + 페르소나 파일명 옛 형식으로 2026-06-06 세션 4에서 삭제. 대체 = decision_log + glossary + session summary + 본 문서 4종.

---

*최종 갱신: 2026-06-06 by pm_minseok (lead) — 세션 4 N5 안정화 완료 시점*
*다음 갱신: 본 세션 마무리 시 + 후속 세션 종료 시*
