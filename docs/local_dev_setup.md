# 로컬 개발 환경 가이드

> 최종 업데이트: 2026-04-19
> 담당 축: **Where** — 어디서 어떻게 돌리는가
> 관련 문서: `database_schema.md`, `implementation_roadmap.md`

---

## 📌 빠른 참조 (에이전트용)

**이 문서에서 찾을 수 있는 것**
- 필요한 사전 설치 도구 → 1장
- 저장소 클론부터 실행까지 → 2장
- `docker-compose` 구성 → 3장
- 환경 변수 (`.env`) 명세 → 4장
- DB 초기화 및 마이그레이션 절차 → 5장
- 자주 쓰는 개발 명령어 → 6장
- 문제 해결 (Troubleshooting) → 7장

**이 문서에서 찾을 수 없는 것**
- DB 스키마 상세 → `database_schema.md`
- 구현 순서 → `implementation_roadmap.md`
- API 호출 예시 → `api_endpoints.md`

---

## 이 문서는
JLPT 개인 학습 에이전트를 **로컬 머신에서 실행**하기 위한 단계별 가이드입니다.
개발 환경 재현성과 각 에이전트가 실행을 확인할 수 있는 체크 포인트를 제공합니다.

---

## 1. 사전 설치 도구

로컬 개발에 필요한 도구와 권장 버전입니다.

| 도구 | 권장 버전 | 용도 |
|------|-----------|------|
| macOS / Linux | - | 개발 OS (Windows는 WSL2 권장) |
| Docker Desktop | 최신 | 컨테이너 실행 |
| Docker Compose | v2+ | 멀티 컨테이너 오케스트레이션 |
| Python | 3.11.x | 런타임 |
| Poetry | 1.7+ | 패키지 관리 |
| Git | 최신 | 버전 관리 |
| PyCharm (권장) | 2024.x | IDE |
| DataGrip (권장) | 최신 | DB 가시화 |

### 설치 확인

```
docker --version
docker compose version
python --version
poetry --version
git --version
```

---

## 2. 저장소 클론부터 실행까지

### 2-1. 저장소 준비

```
git clone <repo-url> training_jlpt
cd training_jlpt
```

### 2-2. 파이썬 의존성 설치

```
poetry install
```

가상환경은 `.venv` 디렉토리에 생성됩니다.

### 2-3. 환경 변수 파일 생성

`.env.example`을 복사해 `.env`를 만듭니다.

```
cp .env.example .env
```

그 다음 `.env`의 키 값들을 실제 값으로 채웁니다 (4장 참조).

### 2-4. Docker 컨테이너 기동

```
docker compose up -d
```

컨테이너 상태 확인:

```
docker compose ps
```

### 2-5. DB 마이그레이션

```
poetry run alembic upgrade head
```

### 2-6. 애플리케이션 실행

```
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2-7. 동작 확인

```
curl http://localhost:8000/health
# → {"status": "ok", "version": "0.1.0"}
```

---

## 3. docker-compose 구성

`docker-compose.yml`이 기동하는 서비스입니다.

### 3-1. PostgreSQL + pgvector

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
```

**주의**:
- 포트 5432가 로컬에서 사용 중이면 `5433:5432`로 매핑 변경.
- `data/postgres`는 로컬 디렉토리에 볼륨 마운트. `.gitignore`에 포함.

### 3-2. Redis

```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
```

**용도**: LLM 응답 캐시 보조, 익명 세션 임시 저장 (미결 사항).

### 3-3. 앱 서비스 (선택)

개발 중에는 앱 컨테이너보다 **로컬 uvicorn**이 빠릅니다.
프로덕션 테스트 시에만 컨테이너로 실행.

```yaml
  app:
    build: .
    env_file: .env
    depends_on:
      - db
      - redis
    ports:
      - "8000:8000"
```

---

## 4. 환경 변수 명세

`.env` 파일에 정의되어야 할 값입니다.

### 4-1. 필수

| 변수 | 예시 | 설명 |
|------|------|------|
| `POSTGRES_DB` | `jlpt_agent` | DB 이름 |
| `POSTGRES_USER` | `postgres` | DB 유저 |
| `POSTGRES_PASSWORD` | `yoursecretpw` | DB 비밀번호 |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:yoursecretpw@localhost:5432/jlpt_agent` | 앱 연결용 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 연결용 |
| `OPENAI_API_KEY` | `sk-...` | OpenAI API 키 (임베딩 + LLM) |

### 4-2. 선택

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `LLM_MODEL_DEFAULT` | `gpt-4o-mini` | 기본 LLM 모델 |
| `LLM_MODEL_QUALITY` | `gpt-4o` | 품질 필요 시 사용할 모델 |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | 임베딩 모델 |
| `LOG_LEVEL` | `INFO` | 로그 레벨 |
| `SESSION_TOKEN_TTL_HOURS` | `24` | 익명 세션 TTL |

### 4-3. 보안 주의

- `.env`는 **절대 Git에 커밋하지 않습니다.** `.gitignore`에 포함.
- `.env.example`만 저장소에 두어 템플릿 역할.
- `OPENAI_API_KEY`는 비용이 발생하므로 키 유출 주의.

---

## 5. DB 초기화 및 마이그레이션

### 5-1. 최초 1회 설정

```
# 컨테이너 기동
docker compose up -d db

# extension 수동 확인 (이미지에 포함되어 있지만 혹시 모를 경우)
docker compose exec db psql -U postgres -d jlpt_agent -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose exec db psql -U postgres -d jlpt_agent -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
```

### 5-2. Alembic 마이그레이션 적용

```
# 최신으로 업그레이드
poetry run alembic upgrade head

# 한 단계 다운그레이드
poetry run alembic downgrade -1

# 현재 리비전 확인
poetry run alembic current
```

### 5-3. 새 마이그레이션 생성

```
poetry run alembic revision --autogenerate -m "add_weak_points_table"
```

생성된 파일은 `src/db/migrations/versions/`에 들어갑니다.
**반드시 리뷰 후 수정**하세요. autogenerate는 pgvector 컬럼 타입 등 일부를 놓치는 경우가 있습니다.

### 5-4. seed 데이터 적재

```
# 진단 문제 seed
poetry run python src/scripts/seed_diagnosis_questions.py

# 문법 청크 import
poetry run python src/scripts/import_grammar_chunks.py

# 임베딩 생성
poetry run python src/scripts/embed_grammar_chunks.py
```

### 5-5. DataGrip으로 DB 확인

| 항목 | 값 |
|------|----|
| Host | `localhost` |
| Port | `5432` |
| Database | `jlpt_agent` |
| User | `postgres` |
| Password | `.env` 참조 |

---

## 6. 자주 쓰는 개발 명령어

### 6-1. 앱 실행

```
# 개발 모드 (hot reload)
poetry run uvicorn src.api.main:app --reload

# 특정 포트로
poetry run uvicorn src.api.main:app --reload --port 8080
```

### 6-2. 테스트

```
# 전체
poetry run pytest

# 특정 디렉토리
poetry run pytest tests/api/

# 특정 마커
poetry run pytest -m "not slow"

# 커버리지
poetry run pytest --cov=src --cov-report=term-missing
```

### 6-3. 린트 / 포맷

```
# Ruff (린트)
poetry run ruff check src/

# Ruff (자동 수정)
poetry run ruff check --fix src/

# Black (포맷)
poetry run black src/

# mypy (타입 체크)
poetry run mypy src/
```

### 6-4. DB 쉘

```
# psql 직접 접속
docker compose exec db psql -U postgres -d jlpt_agent
```

### 6-5. 컨테이너 관리

```
# 전체 기동
docker compose up -d

# 전체 중지
docker compose down

# 볼륨까지 삭제 (주의: DB 초기화됨)
docker compose down -v

# 로그 실시간 확인
docker compose logs -f db
```

---

## 7. Troubleshooting

### 7-1. 포트 충돌

**증상**: `Error: port is already allocated`

**해결**:
```
# 점유 프로세스 확인
lsof -i :5432

# docker-compose.yml의 포트 매핑 변경
# ports: "5433:5432"
```

### 7-2. pgvector extension 미설치

**증상**: `ERROR: type "vector" does not exist`

**해결**:
```
docker compose exec db psql -U postgres -d jlpt_agent \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 7-3. Alembic autogenerate가 pgvector 컬럼을 놓침

**증상**: 마이그레이션 파일에 `embedding` 컬럼이 빠져 있음.

**해결**: 마이그레이션 파일을 수동 편집하여 아래를 추가.

```python
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

sa.Column('embedding', Vector(1536), nullable=True)
```

### 7-4. asyncpg 연결 에러

**증상**: `ModuleNotFoundError: No module named 'asyncpg'` 또는 `DATABASE_URL` 스킴 오류

**해결**:
- 비동기 URL 스킴은 `postgresql+asyncpg://`여야 함.
- `poetry add asyncpg`로 설치 확인.

### 7-5. OpenAI API rate limit

**증상**: 임베딩 생성 스크립트에서 `RateLimitError`

**해결**:
- 배치 크기를 줄이고 sleep 넣기.
- `src/scripts/embed_grammar_chunks.py`에서 `batch_size`와 `sleep_seconds` 조정.

### 7-6. Docker 볼륨 권한 문제 (Linux)

**증상**: `Permission denied` on `./data/postgres`

**해결**:
```
sudo chown -R 999:999 ./data/postgres
```

---

## 미결 및 상태 (임시)
> 향후 `projectState.json`으로 이전 예정

- **`.env.example` 파일 작성 필요**: 본 문서 4장 기준으로 생성 (담당: 재현)
- **Windows WSL2 가이드**: 필요 시 별도 섹션 추가 검토
- **staging / production 환경 가이드**: Phase 3 배포 검토 시 추가