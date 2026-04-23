# AGENTS.md — Common Agent Operating Rules

> recently update : 2026-04-20

Common behavioral rules shared by all agents, regardless of role, tool, or project.
For project-specific domain knowledge, see CLAUDE.md.
For role identity and persona, see prompts/{role}_prompt.md.

## [INFORM] How to Read Project Context
1. AGENTS.md (this file): common behavioral rules — HOW to act
2. CLAUDE.md: project domain knowledge — WHAT this project is
3. prompts/{your_role}_prompt.md: your persona and role boundary — WHO you are
4. {working_dir}/AGENTS.md (if present): local rules for that directory

When information appears in multiple files, the more specific file wins:
directory-local > project (CLAUDE.md) > common (this file).

## [CONSTRAIN] File Boundaries (common principles)
- Never access paths outside the project root
- Never touch system paths (/etc/, /usr/, etc.)
- Never modify virtual environments (.venv/, node_modules/, etc.)
- Never read or modify environment files (.env)
- Project-specific writable/read-only paths are defined in CLAUDE.md

## [CONSTRAIN] Tool Usage (common policy)
- Allowed: file I/O within project, test runners, build tools,
  git (read-only operations)
- Blocked: curl, wget, sudo, rm -rf, chmod, git push --force
- Project-specific tool commands (pytest, alembic, etc.) are in CLAUDE.md
- Rationale: external network calls and system modifications require
  explicit human decision

## [CONSTRAIN] Resource Limits
- Max tool calls per task: 100
- Same-file edit limit: 5 (reconsider approach after 3)
- Session timeout: 60 minutes

## [CONSTRAIN] Approval Required (common gates)
- File deletion
- Dependency addition or removal
- Deleting or skipping existing tests
- Infrastructure config changes (Docker, CI, etc.)
- Modifying files outside your role boundary
- Modifying AGENTS.md, CLAUDE.md, or prompts/*
- Project-specific approval gates are defined in CLAUDE.md

## [VERIFY] Verification Discipline
- Run project-standard verification before declaring task complete
  (specific commands in CLAUDE.md)
- New feature requires new test — untested code is incomplete
- Assertions must reflect *intended behavior*, not actual output
- Do NOT modify mocks or assertions to bypass failures
- Do NOT use `# type: ignore`, `eslint-disable`, or similar to bypass checks

## [CORRECT] When Things Fail
- Same approach fails 3 times → try a different strategy
- 5 total failures → stop and report to human
- Same error message 3 times → escalate immediately
- Do NOT rewrite entire file on test failure — fix the specific cause

## [CORRECT] Loop Detection
- Track file edit counts per session
- Same file edited > 5 times → reconsider approach
- Total edits > 30 without passing verification → escalate
- Same error recurring 3+ times → escalate immediately

## [CORRECT] Failure Logging
- Every significant failure adds 1 prevention rule
  to CLAUDE.md §Past Failures → Rules
- Format: `YYYY-MM-DD — what happened → what to do instead`
- Never delete old rules — they are project memory

## [CONSTRAIN] Scope Discipline
- No out-of-scope refactoring
- Report discovered issues; do not fix them silently
- When requirements are unclear, ask — do not guess

## [CONSTRAIN] Role Boundary & Handoff
- Each agent operates within the role defined in prompts/{role}_prompt.md
- Cross-role decisions require an explicit handoff note
- Handoff format: "{name}님 확인 필요: {reason}"
- Handoff must include: context summary, decision needed,
  work completed so far

## [INFORM] Reporting Format
When declaring task complete, include:
1. List of changed files
2. Verification results (tests / lint / type check)
3. Unresolved items (if any)
4. Issues discovered but not modified