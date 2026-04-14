# 로컬 개발 환경 세팅

> 최종 업데이트: 2026-04-14
> 이 저장소를 로컬에서 재현 가능한 상태로 실행하기 위한 가이드입니다.

---

## 1. 사전 요구사항

- Docker Desktop
- Python 3.11
- Poetry
- DataGrip 또는 다른 PostgreSQL 클라이언트

---

## 2. 환경변수

`.env`를 만들고 `OPENAI_API_KEY` 값을 설정합니다.

```bash
cp .env.example .env
```

---

## 3. 인프라 실행

로컬 서비스를 실행합니다.

```bash
docker compose up -d
```

현재 서비스 구성:

| 서비스 | 이미지 | 포트 | 용도 |
|--------|--------|------|------|
| `jlpt_postgres` | `pgvector/pgvector:pg16` | `5432` | PostgreSQL 16 + pgvector |
| `jlpt_redis` | `redis:7-alpine` | `6379` | 응답 캐시 |

상태 확인:

```bash
docker compose ps
```

중지:

```bash
docker compose down
```

데이터까지 초기화:

```bash
docker compose down -v
```

---

## 4. 데이터베이스 준비

초기 마이그레이션에서 `pgvector` extension을 활성화해야 합니다.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

권장 PostgreSQL 연결값:

| 항목 | 값 |
|------|----|
| Host | `localhost` |
| Port | `5432` |
| Database | `jlpt_db` |
| User | `jlpt_user` |
| Password | `jlpt_password` |

---

## 5. Python 의존성 설치

```bash
poetry install
```

---

## 6. 트러블슈팅

1. `docker compose ps`로 상태를 확인합니다.
2. 두 컨테이너가 모두 healthy인지 확인합니다.
3. `.env`의 PostgreSQL 접속 정보를 확인합니다.
4. DB 클라이언트에 PostgreSQL 드라이버가 설치됐는지 확인합니다.
