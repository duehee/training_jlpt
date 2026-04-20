# JLPT 개인 학습 에이전트

> JLPT 학습자의 약점을 AI가 진단하고, 맞춤형 문법 학습 경로를 제공하는 서비스

단순한 챗봇이 아니라 **진단 → 검색 → 설명 → 분기형 학습 흐름**을 하나로 묶은 적응형 학습 에이전트입니다.

---

## 배경

저 본인의 **JLPT N2 불합격** 경험에서 출발했습니다.
문제집을 폈을 때 "뭐부터 해야 할지 모르겠다"는 문제를 AI로 풀어보고,
이런 본인의 부족한 부분을 채우고자 만들어보는 프로젝트입니다. 

---

## 타깃 사용자

- JLPT N5~N3 독학 학습자 (주 타깃)
- 현재 수준과 다음 학습 포인트를 모르는 학습자
- N2~N1 독해/청해 보강이 필요한 학습자 (확장 타깃)

---

## 핵심 기능 (Phase 1)

| 기능 | 설명 |
|------|------|
| 익명 진단 | 가입 없이 10문항(N5~N3)으로 레벨 판정 + 약점 추출 |
| 약점 기반 추천 | 진단/학습 이력 기반으로 다음 문법 포인트 제시 |
| RAG 기반 설명 | `pgvector` retrieval로 문법/비교 청크를 가져와 LLM이 설명 생성 |
| 이해도 확인 루프 | 4지선다 확인 문제 → 정오답 분기 (오답 3회 시 우회) |
| 이어하기 | 재방문 시 마지막 학습 지점부터 재개 |

---

## 기술 스택

- **Backend**: FastAPI + async SQLAlchemy 2.0
- **DB**: PostgreSQL 16 + pgvector
- **Cache**: Redis (LLM 응답 캐시)
- **Agent**: LangGraph (분기형 학습 워크플로우)
- **LLM**: OpenAI GPT-4o-mini (기본) / GPT-4o (품질 필요 경로)
- **Embedding**: OpenAI text-embedding-3-small
- **Infra**: Docker Compose

기술 선택 근거는 [`docs/decisionLog.md`](docs/decisionLog.md) 참조.

---

## 현재 상태

- **Phase 1 설계 완료** — 플로우, DB 스키마, API 계약, 데이터 파이프라인 문서화 완료
- **Stage 0 착수 준비** — 기반 골격 구현 단계
- 로드맵 상세: [`docs/implementationRoadmap.md`](docs/implementationRoadmap.md)

---

## 시작하기

로컬 실행 방법은 [`docs/localDevSetup.md`](docs/localDevSetup.md)를 참조하세요.

```bash
docker compose up -d
poetry install
poetry run alembic upgrade head
poetry run uvicorn src.api.main:app --reload
```

---

## 더 자세히

- **설계 문서**: [`docs/`](docs/) — 제품 배경, 플로우, DB 스키마, API, 데이터 파이프라인, 의사결정 로그
- **에이전트 프롬프트**: [`prompts/`](prompts/) — 역할 분리형 협업을 위한 4명의 에이전트 페르소나 (PM/AI·백엔드/데이터/검수)
- **개발 규칙**: [`CLAUDE.md`](CLAUDE.md)