# AGENTs.md — 공통 에이전트 운영 규칙

## File Boundaries
- Project root: ~/PycharmProjects/training_jlpt/
- Writable: src/, tests/, docs/ (with role permission)
- Read-only: pyproject.toml, poetry.lock, docker-compose.yml, .env
- Forbidden: .venv/, /etc/, /usr/, system paths

## Tool Allowlist
- File I/O: Read, Edit, Write (project root only)
- Shell: pytest, poetry run *, alembic *, git (add/commit/status/diff/log)
- Blocked: curl, wget, sudo, rm -rf, chmod, git push --force

## Resource Limits
- Max tool calls per task: 100
- Same-file edit limit: 5 (reconsider after 3)
- Session timeout: 60 minutes

## Testing Rules
- After code change: run `pytest` before reporting complete
- Assertions reflect intended behavior, not actual output
- No it.skip / @pytest.mark.skip without approval
- No `# type: ignore` to bypass failing checks
- Do not modify mocks solely to pass failing tests

## Approval Required
- File deletion
- New dependency installation
- Database schema modification (Alembic)
- Deleting or skipping existing tests
- Modifying test files when task is not test-related
- Cross-role boundary changes (see role prompts)

## Role Boundary
- Each agent operates within their role's scope (see prompts/{role}_prompt.md)
- Cross-role decisions require explicit handoff note
  ("수진님/민석님/츠쿠야님 확인 필요")