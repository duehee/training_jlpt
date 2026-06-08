# Glossary — 프로젝트 용어 사전

> 최근 업데이트: 2026-06-06 (session_3 종료 시점)
> 작성: pm_minseok (lead)
> 용도: 약어·ID·운영 용어 빠른 참조. 출처 표기로 깊이 추적 가능.

---

## 1. 카테고리 분류 (Taxonomy)

| 용어 | 의미 | 출처 |
|---|---|---|
| **L1** | Level 1 — 문법 대분류 그룹. N5는 9그룹(조사 / 활용 / 문형·표현 / 종조사 / 지시·연체 / 의문 표현 / 시간·수량 표현 / 접속·연결 / 부사류) | `decision_log.md` 2026-04-29 + 2026-04-30 갱신 |
| **L2** | Level 2 — L1 하위 소분류 (예: 조사 → 主題조사 / 格조사 / 副조사). N5 기준 약 37~39개 | `02_n5_category_taxonomy.md` |
| **L3** | Level 3 — 항목별 JSON 메타 태그 (검색·필터링용). `connection_type`, `polarity` 등 | `05_n5_l3_tag_assignment_v1.md` |

---

## 2. JLPT 레벨 / BORDER

| 용어 | 의미 |
|---|---|
| **N5 / N4 / N3 / N2 / N1** | JLPT 시험 레벨. 숫자 ↓ = 난이도 ↓ (N5 최저, N1 최고). Phase 1은 N5~N3 진단 범위 |
| **BORDER** | N5와 N4 경계에 있는 문법 항목. 진단·학습에서 별도 처리 (N5/N4 동시 노출 정책) |
| **border_candidate** | L3 boolean 태그. `true` = BORDER 항목 |
| **유효 BORDER 21개** | session_3 츠쿠야 검수 후 N5 BORDER 최종 개수 (23 - 035 중복 -1 - 040 오류 -1). E-7 variant 3건 BORDER 사유는 세션 4 v2 재검수에서 평가 |

---

## 3. 결정 추적 (Decision Log)

`docs/decision_log.md`에 누적. 정빈님 확정 결정만 ID 부여.

| 패턴 | 의미 |
|---|---|
| **D-1 ~ D-7** | 2026-04-28 결정 (예: D-7 = URL path snake_case) |
| **P-1 ~ P-5** | 2026-04-29 [DB][ARCH][STACK] 결정 (P-1 α baseline / P-2·P-3 docker-compose 미사용 / P-5 Python 3.12) |
| **Q1 ~ Q8** | 2026-04-29 정빈님 답변 형식 ID (`session_2/answers.md`) |
| **Decision A/B/C/D** | 2026-04-30 Round 2 결정 (A: BORDER 7 추가 / B: 부사 14 추가 / C: 비교쌍 24쌍 / D: decision_log 누락 추기) |
| **E-1 ~ E-13** | session_3 lead → 정빈님 에스컬레이션. 4/30: E-1~E-4 / 6/5: E-5~E-9 / 6/6: E-10~E-13 |
| **Q5, Q6** | 운영/도구 결정 (Q5 openpyxl 의존성 / Q6 point embedding 길이) |
| **decision_log** | `docs/decision_log.md`. 결정 누적 + 영향 범위 명시. lead 단독 갱신 가능 (정빈님 사전 승인 필요) |

---

## 4. 에스컬레이션 / 검수 이슈

| 용어 | 의미 |
|---|---|
| **E-N** | lead → 정빈님 에스컬레이션 ID. session_3에서 **E-1 ~ E-13** (4/30 E-1~E-4 / 6/5 E-5~E-9 / 6/6 E-10~E-13) |
| **Q-N** | 운영/도구 결정 요청 ID (PM이 정빈님에 질문 단위로 부여). Q5 openpyxl, Q6 embedding 길이 |
| **ISSUE-NN** | 검수 보고서 내 이슈 ID. 보고서마다 01부터 재시작 |
| **HIGH / MEDIUM / LOW** | 검수 이슈 우선순위. HIGH = 구조/오류 즉시 수정, MEDIUM = 정합성, LOW = 권고 |
| **🔴 / ⚠️ / 🟢** | HIGH / MEDIUM / LOW 시각 표기 |

---

## 5. 데이터 식별자

| 패턴 | 의미 | 예 |
|---|---|---|
| **grammar_n5_NNN** | N5 문법 항목 고유 ID (001 ~ 110, base **109개** E-12 정정 후). 세션 4 v2에서 신규 5건 (106~110) ID 부여, 061 제거로 인한 gap 존재 | `grammar_n5_001` = は |
| **grammar_n5_NNN_{variant}** | 이형태 서픽스 ID (E-7, E-11). variant 3건 = `_informal` / `_keisiki` / `_alt` | `grammar_n5_026_informal` = ちゃいけない (026 てはいけない 구어) |
| **compare_n5_XXX_YYY** | 비교 청크 ID. 두 grammar_point_id 결합. **25쌍** (E-5 -1, E-6/E-10 -1, **E-16 +3** 적용 후) | `compare_n5_001_002` = は vs が |
| **chunk_id** | 청크 고유 식별자 (point/compare/variant 모두 포함) | — |

---

## 6. 출처 풀 (Source Pool)

| ID | 출처 | 가중치 |
|---|---|---|
| **SRC-01** | JEES Can-do (능력 척도) | 표준 |
| **SRC-02** | Genki I/II 교재 | 표준 |
| **SRC-03** | みんなの日本語 | 표준 |
| **SRC-04** | TRY! 시리즈 | 표준 |
| **SRC-05** | (수진 산출물 출처 풀 §1-2 참조) | — |
| **SRC-07** | jlptsensei.com (시험 패턴) | 0.5 (보조) |

> 정확한 SRC-04~06은 `docs/planning/session_2/de_sujin/01_n5_master_list.md` §1-2 참조.

---

## 7. 가중치 (★ Star)

| 표기 | 의미 |
|---|---|
| **★★★** | 학습 우선순위 최상 (한국어 학습자 최빈 혼동 / 시험 빈출 핵심). E-8 후 #4 だけ/しか, #14 から/ので 추가 |
| **★★☆** | 중상 |
| **★☆☆** | 중 (이형태 비교, 보조 참조 등) |

---

## 8. 청크 타입 / RAG

| 용어 | 의미 |
|---|---|
| **point** | 단일 문법 항목 청크 (개별 grammar_point) |
| **compare** | 비교 청크 (두 항목 비교) |
| **variant** | 이형태 청크 (E-7, E-11). base 항목과 구분, `variant_chunks` 시트 분리 |
| **embedding_text** | RAG 임베딩 대상 텍스트. 청크 내 별도 필드 |
| **compare 길이 스펙** | 50~100자 (RAG 짧고 정밀 매칭) |
| **point 길이 스펙** | **150~270자** (Q6 결정 정식 채택) |
| **RAG** | Retrieval-Augmented Generation. pgvector + text-embedding-3-small |

---

## 9. L3 메타 태그 (JSON enum)

| 태그 | 값 | 비고 |
|---|---|---|
| **connection_type** | `verb_te` / `i_adj_ku` / `na_adj_de` / `noun_de` / `plain` / `null` | 조사류 = `null` (수진 결정) |
| **polarity** | `positive` / `negative` / `both` | |
| **tense** | `non_past` / `past` / `any` | |
| **formality** | `polite` / `plain` / `both` | |
| **border_candidate** | `boolean` | BORDER 항목 플래그 |
| **comparison_pair** | `string[]` (grammar_point_id 배열) | **E-9 확정: 비교 청크 생성 트리거**. taxonomy **25쌍** (E-16 +3 후)이 단일 진실 |
| **interrogative_type** | `thing` / `place` / `time` / `person` / `quantity` / `reason` / `manner` | 의문사 분류. E-1 후 yes_no 제거 |
| **counter_class** | `object` / `person` / `order` / `currency` | 조수사 분류 |

---

## 10. 운영 용어 (Agent Teams 모드)

| 용어 | 의미 |
|---|---|
| **lead** | 팀 리더 (현 세션 = `pm_minseok`). 사용자(정빈님) 단일 통신 채널 |
| **teammate** | 팀원 (`be_jaehyeon`, `de_sujin`, `jp_tsukuya`) |
| **spawn** | `Agent` 도구로 teammate 생성. 모델·이름·team_name 지정 |
| **kickoff** | 세션 시작 spawn 프로토콜. 템플릿: `prompts/_spawn_templates/kickoff.md` |
| **broadcast** | lead 전용 전체 공지 (비용 큼, ≤5회/세션) |
| **message** | `SendMessage`, 1:1 통신. teammate 간 직접 message 가능 (조건부) |
| **plan_approval_request / response** | teammate plan 승인 요청·응답. lead 단독 승인 금지 — 정빈님 게이트 |
| **permission_request** | 도구 권한 요청. teammate가 Write/Edit 등 호출 시 lead 인박스 라우팅 → ~40초 미응답 시 자동 거부. 사전 jq 명령으로 본문 회수 가능 |
| **idle_notification** | teammate 턴 종료 자동 알림. 본문 없는 시스템 메시지 |
| **task_assignment** | 시스템 task 부여 알림. **lead의 명시적 ack가 아님** (CLAUDE.md §과거 실패) |
| **graceful shutdown** | teammate 종료 요청 (`shutdown_request` 메시지) |

---

## 11. 팀 역할 식별자

| 이름 | 역할 | 페르소나 파일 | 권장 모델 |
|---|---|---|---|
| **pm_minseok** (민석) | PM Lead — 운영·결정·핸드오프 관리 | `prompts/pm_minseok_prompt.md` | opus 4.7 (lead) |
| **be_jaehyeon** (재현) | Senior Backend / AI Engineer (RAG / FastAPI / Alembic / Docker) | `prompts/be_jaehyeon_prompt.md` | sonnet |
| **de_sujin** (수진) | Data Engineer (수집·청킹·메타데이터 설계) | `prompts/de_sujin_prompt.md` | sonnet |
| **jp_tsukuya** (츠쿠야) | QA Lead / 일본어 native 검수 | `prompts/jp_tsukuya_prompt.md` | **opus 4.7 (정밀도 우선, session_3 검증됨)** |

---

## 12. Phase / Stage / Session

| 용어 | 의미 |
|---|---|
| **Phase 1** | 프로젝트 1단계 범위 — N5~N3 진단 + 학습 기록 (프로덕션 수준) |
| **Stage 0** | 인프라 골격 — Docker 환경 / FastAPI 엔트리 / Alembic α baseline |
| **Stage 1+** | 후속 Stage (RAG 파이프라인 / 진단 워크플로우 등). `docs/implementation_roadmap.md` 참조 |
| **session_N** | 세션 번호. lead 자동 증가 금지, 정빈님 수동 부여 |
| **MVP 12 테이블** | DB MVP 설계 (재설계 후 확정, 2026-06-08). `chunks` 통합 + `comparison_pairs` seed + `diagnostic_questions` 신설 + 도메인 9 계승. 단일 진실 = `docs/planning/session_4/be_jaehyeon/00_db_overview.md` |
| **α baseline** | Alembic 빈 baseline (스키마 0 상태) |

---

## 13. 운영 정정 / 실패 규칙

`CLAUDE.md §과거 실패 → 규칙` 통합 완료 (6/5).

| 날짜 | 규칙 |
|---|---|
| **2026-04-28** | sonnet teammate Write + plan 승인 동시 발생 시 ink crash → 산출물은 SendMessage 본문 → lead 저장 (지금은 메커니즘 재해석됨, ↓ 4/30 참조) |
| **2026-04-29** | task_assignment 시스템 알림 ≠ lead 명시적 ack. spawn prompt에 명시 |
| **2026-04-30** (메커니즘) | 도구 권한 요청은 `permission_request` JSON으로 lead 인박스 라우팅 (~40초 timeout 자동 거부). 우회: 정빈님 화면 prompt 승인 / 사전 jq로 본문 회수 / 디스크 직접 Write |
| **2026-04-30** (운영) | lead path CC 강제력 한계 — spawn prompt에 권고지 강제 아님 톤. 디스크 저장이 진실, lead 디스크 Read 안전망 |
| **2026-06-05** (장기 정지) | 1개월 이상 정지 후 teammate Agent 생존 불명 + 컨텍스트 캐시 만료. 옵션 A(ping) 또는 옵션 B(cleanup 후 재spawn)로 확인 |

---

## 14. 검수 결과 등급 (츠쿠야)

| 표기 | 의미 |
|---|---|
| **✅ 승인** | 수정 불필요 |
| **⚠️ 수정 요청** | 부분 수정 후 승인 |
| **❌ 오류** | 수정 필수 |
| **🔴 P1 / ⚠️ P2 / 🟢 P3** | 우선순위 (HIGH/MEDIUM/LOW와 매핑) |

---

## 15. 도구 / 환경

| 용어 | 의미 |
|---|---|
| **`.venv`** | 프로젝트 Python 가상환경 (`/Users/duehee/PycharmProjects/training_jlpt/.venv`) |
| **openpyxl** | Python xlsx 라이브러리. **3.1.5 설치 완료** (Q5 승인, 6/6) |
| **pgvector** | PostgreSQL 벡터 확장 Python 바인딩. **0.4.2 설치** (openpyxl 의존성 그래프 부수 효과) |
| **MCP 서버** | postgres / context7. CLAUDE.md §MCP 서버 참조 |
| **TeamCreate / TeamDelete** | 팀 생성·삭제 도구 |
| **TaskCreate / TaskUpdate** | 작업 추적 도구 (팀 단위 task list 공유) |

---

## 16. 운영 데이터 디렉터리 (`data/`)

E-13 결정 (2026-06-06) — xlsx 운영 진실 공급원 분리.

| 위치 | 내용 |
|---|---|
| `data/n5/n5_master.xlsx` | N5 마스터 5 시트 (`master_list` **109 base** (E-12 정정 후) + `taxonomy_def` + `l3_assignment` + `border_meta` + `variant_chunks` 3건) |
| `data/n5/n5_comparison.xlsx` | N5 비교쌍 2 시트 (`comparison_pairs` **25쌍** (E-16 +3 후) + `comparison_chunks` 본문) |
| `data/schema/n5_master_schema.md` | 마스터 xlsx 컬럼 명세 (헤더·타입·필수) |
| `data/schema/n5_comparison_schema.md` | 비교쌍 xlsx 컬럼 명세 |
| `data/{n4,n3}/` | 추후 N4/N3 작업 진입 시 동일 패턴 신설 |

**정책**: xlsx = 운영 진실 / MD = 검수·협업 친화 (`docs/planning/session_N/de_sujin/`에 별도 유지) / DB = xlsx → 적재 파이프라인 (Stage 1 또는 트랙 3에서 lead/재현 설계)

---

## 출처 문서 빠른 참조

| 알고 싶은 것 | 어디 보면 됨 |
|---|---|
| 프로젝트 도메인 | `CLAUDE.md` |
| 공통 에이전트 규칙 | `AGENTs.md` |
| 정빈님 결정 누적 | `docs/decision_log.md` |
| DB 스키마 | `docs/database_schema.md` |
| API 엔드포인트 | `docs/api_endpoints.md` |
| 구현 순서 | `docs/implementation_roadmap.md` |
| 협업 가이드 | `docs/agent_guide.md` |
| 세션별 산출물 | `docs/planning/session_N/{teammate}/` |
| 페르소나 | `prompts/{teammate}_prompt.md` |
| spawn 템플릿 | `prompts/_spawn_templates/kickoff.md` |
| **운영 데이터 (xlsx)** | `data/{level}/` |
| **xlsx 스키마 명세** | `data/schema/` |

---

*신규 약어·ID 패턴 등장 시 lead가 본 문서에 추가. 정빈님이 직접 추가 요청하셔도 OK.*
