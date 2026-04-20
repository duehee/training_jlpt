# CLAUDE.md — JLPT Agent Project v1.0

## [INFORM] Project Overview
Personal management AI agent for JLPT learners.
RAG-based diagnosis of weak grammar points with spaced repetition learning.
Phase 1 scope: N5~N3 diagnosis + learning records (production-grade).

## [INFORM] Architecture
- Backend: FastAPI + async SQLAlchemy 2.0
- DB: PostgreSQL 16 + pgvector
- Agent: LangGraph workflow
- LLM: OpenAI (GPT-4o-mini default, GPT-4o for quality-critical paths)
- Cache: Redis (LLM response cache)
- Embedding: text-embedding-3-small
- Infra: Docker Compose
- Detailed rationale: docs/agent_guide.md, docs/decision_log.md

## [CONSTRAIN] Conventions (NON-NEGOTIABLE)
- Python: snake_case for functions/variables, PascalCase for classes
- Files: snake_case
- Type hints on all public functions — no bare `Any`
- Pydantic for all API request/response models
- Async by default for I/O (DB, LLM, HTTP)

## [CONSTRAIN] File Boundaries
- Writable: src/, tests/, src/db/migrations/versions/
- Read-only: pyproject.toml, poetry.lock, docker-compose.yml
- Forbidden: .env, .venv/, /etc/, /usr/

## [CONSTRAIN] Tool Allowlist
- File I/O: Read, Edit, Write (project root only)
- Shell: pytest, poetry run *, alembic *,
        git (add/commit/status/diff/log)
- Blocked: curl, wget, sudo, rm -rf, chmod, git push --force

## [CONSTRAIN] Approval Required
- Alembic migrations
- New dependency installation (`poetry add`)
- Docker Compose service changes
- Deleting or skipping existing tests
- Modifying LLM/vector store abstraction interfaces

## [CONSTRAIN] Resource Limits
- Max tool calls per task: 100
- Same-file edit limit: 5 (reconsider after 3)
- Session timeout: 60 minutes

## [VERIFY] Verification Requirements
- Run `pytest` after any code change — no exceptions
- Run `mypy src/` after modifying .py files
- Run `ruff check src/` after modifying .py files
- New feature = new test. No untested code.

## [VERIFY] Self-Verification Checklist
Before declaring task complete, verify:
1. All existing tests still pass
2. New code has corresponding tests
3. No mypy/pyright errors on modified files
4. Ruff formatting applied
5. Async code uses proper await (no sync-in-async)
6. LLM calls go through cache layer
7. DB access uses async session
8. Naming conventions followed

## [VERIFY] Eval Baseline
See eval/jlpt_eval.py. Key areas:
- rag_retrieval_accuracy (threshold: 0.9, runs: 10)
- llm_cache_hit (threshold: 1.0, runs: 3)
- diagnostic_flow_e2e (threshold: 0.85, runs: 5)
- embedding_crosslingual (threshold: 0.8, runs: 10)

## [CORRECT] Error Recovery
- On test failure: read error message, analyze root cause,
  fix the specific issue (do NOT rewrite entire file)
- Max retries on same approach: 3
- After 3 failures: try alternative implementation strategy
- After 5 total failures: stop and report to human

## [CORRECT] Loop Detection
- Track file edit counts per session
- Same file edited > 5 times: reconsider approach
- Total edits > 30 without test passing: escalate
- Same error message 3+ times: escalate immediately

## [CORRECT] Failure Logging
- Every significant failure adds 1 prevention rule
  to the "Past Failures → Rules" section
- Format: YYYY-MM-DD — what happened → what to do instead
- Never delete old rules — they are project memory

## [INFORM] Past Failures → Rules
- Direct LLM call without caching → must go through cache layer
- Direct `openai` library call → must use provider abstraction
- Schema change without Alembic migration → data loss risk, forbidden
- Mixing sync DB session in async context → always use async session
- Overuse of GPT-4o → default to 4o-mini, use 4o only for quality paths
- (Accumulate future failure cases here)

## [INFORM] MCP Servers
- postgres: DB schema and query inspection
- context7: Latest docs for FastAPI / SQLAlchemy / LangGraph

## Scope
- No out-of-scope refactoring
- Report discovered issues, do not fix silently
- Ask when blocked on unclear requirements

## Reference
- docs/agent_guide.md, docs/database_schema.md
- docs/decision_log.md, docs/api_endpoints.md
- docs/implementation_roadmap.md, docs/service_flows.md
- Role prompts: prompts/