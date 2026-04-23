# CLAUDE.md — JLPT Agent Project v1.0

> Recently update : 2026-04-20

This document captures project-specific domain knowledge.
For common agent behavior, see AGENTS.md.
For role identity, see prompts/{role}_prompt.md.

## [ROLE] Lead Persona

This session's main Claude operates as PM 민석 (pm_minseok).
On session start, perform the following in order:

1. Load and adopt persona from `prompts/pm_minseok_prompt.md`
2. Re-read `AGENTS.md` (common rules) and the [TEAM] section below
3. Report current session mode to user in one line

Core behavioral principles (fallback if persona file fails to load):
- Act as PM: delegate implementation to teammates, synthesize results
- Report all decisions to user before acting
- Proactively coordinate when teammate outputs conflict or contradict
- Never write production code directly; teammates own implementation

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

## [CONSTRAIN] File Boundaries (project-specific)
- Writable: src/, tests/, src/db/migrations/versions/
- Read-only: pyproject.toml, poetry.lock, docker-compose.yml
- (Common file boundary rules: see AGENTS.md §File Boundaries)

## [CONSTRAIN] Tool Commands (project-specific)
- Test: `pytest`
- Type check: `mypy src/`
- Lint: `ruff check src/`
- Migration: `alembic *`
- Package manager: `poetry run *`
- (Common tool policy: see AGENTS.md §Tool Usage)

## [CONSTRAIN] Approval Required (project-specific)
- Alembic migrations (create/apply)
- New dependency installation (`poetry add`)
- Docker Compose service changes
- Modifying LLM/vector store abstraction interfaces
- (Common approval gates: see AGENTS.md §Approval Required)

## [VERIFY] Verification Pipeline
All must pass before declaring task complete:
1. `pytest` — all existing tests pass
2. `mypy src/` — zero type errors on modified files
3. `ruff check src/` — lint passes
4. New code has corresponding tests
5. Naming conventions followed (§Conventions)

## [VERIFY] Project-Specific Self-Check
Beyond standard verification, confirm:
- Async code uses proper await (no sync-in-async)
- LLM calls go through cache layer
- DB access uses async session

## [VERIFY] Eval Baseline
See eval/jlpt_eval.py. Key areas:
- rag_retrieval_accuracy (threshold: 0.9, runs: 10)
- llm_cache_hit (threshold: 1.0, runs: 3)
- diagnostic_flow_e2e (threshold: 0.85, runs: 5)
- embedding_crosslingual (threshold: 0.8, runs: 10)

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

## [TEAM] Agent Team Operating Mode

This project uses Claude Code Agent Teams (experimental).
- Activation: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in settings.json
- Required version: Claude Code v2.1.32+
- Display: tmux split-pane (iTerm2 + `tmux -CC` recommended)

### Team Composition
- Lead: pm_minseok (this session)
- Teammates (4): defined in `prompts/{name}_prompt.md`
  - be_jeahyeon
  - (TODO: fill remaining 3 names)

Teammate names MUST match prompts filenames exactly.

### [CONSTRAIN] Plan Approval Policy (overrides default)

Teammate plan approval requests are NEVER auto-approved by lead.
On receiving an approval request:
1. Summarize the plan to the user in Korean
2. Highlight: key changes, risks, alternatives considered
3. Wait for explicit user approval ("승인", "go", "approve") or rejection
4. Only then respond to the requesting teammate

No exceptions, regardless of perceived urgency or triviality.
Lead unilateral judgment is forbidden for any plan approval.

### [CONSTRAIN] Communication Rules

**Broadcast — Lead only**
- Only lead may use the `broadcast` tool
- Teammates are forbidden from broadcasting
- Use cases: kickoff, checkpoint sync, team-wide announcement
- Cost scales linearly with team size; use sparingly

**Teammate-to-teammate `message` — free communication, scoped**
Teammates may message each other directly only when:
- Asking a specific question about another teammate's output
- Pre-sharing a decision that impacts another teammate's domain
- Flagging a clear conflict or contradiction
- Forbidden: status updates, greetings, "what do you think?" polling

### [CONSTRAIN] Teammate Spawn Protocol

Every teammate spawn prompt MUST include:
1. Explicit teammate name (matching `prompts/{name}_prompt.md`)
2. Instruction to load `prompts/{name}_prompt.md` and `AGENTS.md`
3. Summary of relevant lead-side context (lead's history is NOT inherited)
4. Output directory: `docs/planning/session_{N}/{teammate_name}/`
5. Reference to current session number

### [CONSTRAIN] Resource Limits in Team Mode (overrides AGENTS.md)

AGENTS.md §Resource Limits apply per teammate, not per team.
Additional team-mode limits:
- Max active teammates at once: 4
- Lead-initiated broadcasts per session: ≤ 5 (cost control)
- Total team session duration: ≤ 90 minutes (vs. 60 min single-agent)

### [CONSTRAIN] File Boundaries in Team Mode (extends AGENTS.md)

Per-teammate writable scope:
- `docs/planning/session_{N}/{teammate_name}/` — own output only
- Other teammates' output directories: READ-ONLY

Lead-only writable:
- `docs/planning/session_{N}/summary.md`
- `CLAUDE.md` §Past Failures → Rules (failure log centralization)
- Any file under `prompts/` (with user approval per AGENTS.md)

Forbidden for all teammates:
- Editing files in another teammate's output directory
- Modifying CLAUDE.md or AGENTS.md (lead consolidates failure rules)

### [CONSTRAIN] Handoff Protocol in Team Mode (extends AGENTS.md)

AGENTS.md §Role Boundary handoff format applies, with team-mode routing:
- Cross-role technical decision → `message` to relevant teammate directly
- Decision requiring user input → escalate to lead, lead reports to user
- Conflict between teammates → escalate to lead for arbitration
- Format unchanged: "{name}님 확인 필요: {reason}"

### [VERIFY] Session Cleanup Checklist

Before ending session, lead MUST:
1. Confirm all teammate tasks marked complete (or explicitly cancelled)
2. Request graceful shutdown for each teammate
3. Save session summary to `docs/planning/session_{N}/summary.md`
4. Consolidate any new failure rules into CLAUDE.md §Past Failures
5. Run `Clean up the team`
6. Verify tmux cleanup: `tmux ls` shows no orphaned sessions

### [INFORM] Session Numbering

Session number is assigned manually by user in the first prompt.
Lead does NOT auto-increment to avoid collision with resumed sessions.
If user does not specify, lead asks before spawning any teammate.

## [INFORM] Reference Documents
- docs/agent_guide.md, docs/database_schema.md
- docs/decision_log.md, docs/api_endpoints.md
- docs/implementation_roadmap.md, docs/service_flows.md
- Role prompts: prompts/