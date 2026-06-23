"""진단 문항 JSON seed → `diagnostic_questions` 적재 (멱등 UPSERT).

사용법:
    poetry run python scripts/seed_diagnostic_questions.py
    poetry run python scripts/seed_diagnostic_questions.py --file scripts/diagnostic_questions_v1.json

입력: 수진 핸드오프(`de_sujin/01_diagnostic_questions_handoff_v1.md` §4) JSON을 직접 소비.
`question_key` UNIQUE 기준 UPSERT — 재실행 안전(N5 chunk 로더 §I-3 동일 패턴).

검증(적재 전 순수): correct_choice ∈ choices 키 / level enum / choices 4지선다 / key 고유.
설계 근거: `docs/planning/session_6/be_jaehyeon/05_diagnostic_seed_plan.md`.
적재 벡터/임베딩 없음 — 진단 문항은 규칙 채점이라 임베딩 불필요.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, model_validator
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# 프로젝트 루트를 import 경로에 추가 (직접 실행 대비)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings  # noqa: E402
from src.db.models import DiagnosticQuestion  # noqa: E402

# 진단 문항 허용 레벨 (Phase 1: N5~N3; seed는 N5/N4). 모델 CheckConstraint와 정합.
ALLOWED_LEVELS: tuple[str, ...] = ("N1", "N2", "N3", "N4", "N5")
DEFAULT_SEED = Path(__file__).resolve().parent / "diagnostic_questions_v1.json"

# 적재 대상 컬럼 (id/created_at/updated_at은 server_default 자동 생성)
_UPSERT_COLUMNS: tuple[str, ...] = (
    "question_key",
    "level",
    "grammar_point_id",
    "stem",
    "stem_furigana",
    "stem_ko",
    "choices",
    "correct_choice",
    "explanation_ko",
)


class Choice(BaseModel):
    """문항 선택지 한 개. text_ko는 선택적 한국어 번역(데이터 확장)."""

    key: str
    text: str
    text_ko: str | None = None


class QuestionSeed(BaseModel):
    """진단 문항 seed 한 건 (적재 전 검증 단위).

    stem_furigana(ruby HTML)·stem_ko(한국어)는 선택적 — 미보강 데이터도 적재 가능.
    """

    question_key: str
    level: str
    grammar_point_id: str
    stem: str
    stem_furigana: str | None = None
    stem_ko: str | None = None
    choices: list[Choice]
    correct_choice: str
    explanation_ko: str | None = None

    @model_validator(mode="after")
    def _check(self) -> QuestionSeed:
        if self.level not in ALLOWED_LEVELS:
            raise ValueError(f"{self.question_key}: level '{self.level}' 비허용")
        keys = [c.key for c in self.choices]
        if len(keys) != 4:
            raise ValueError(f"{self.question_key}: choices는 4개여야 함 (현재 {len(keys)})")
        if len(set(keys)) != len(keys):
            raise ValueError(f"{self.question_key}: choices key 중복 {keys}")
        if self.correct_choice not in keys:
            raise ValueError(
                f"{self.question_key}: correct_choice '{self.correct_choice}' "
                f"가 choices 키 {keys}에 없음 (정답 무결성 위반)"
            )
        return self

    def to_row(self) -> dict[str, Any]:
        """UPSERT용 dict. choices는 JSONB 직렬화 형태로 (text_ko 없으면 키 제외)."""
        return {
            "question_key": self.question_key,
            "level": self.level,
            "grammar_point_id": self.grammar_point_id,
            "stem": self.stem,
            "stem_furigana": self.stem_furigana,
            "stem_ko": self.stem_ko,
            "choices": [c.model_dump(exclude_none=True) for c in self.choices],
            "correct_choice": self.correct_choice,
            "explanation_ko": self.explanation_ko,
        }


def load_seed(path: Path) -> list[QuestionSeed]:
    """JSON seed 로드 + 검증. question_key 전역 고유성까지 확인.

    실패 시 ValueError/ValidationError를 올린다 (적재 전 차단 — DB 무관 순수).
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("seed 최상위는 JSON 배열이어야 함")
    questions = [QuestionSeed.model_validate(item) for item in raw]
    keys = [q.question_key for q in questions]
    dupes = {k for k in keys if keys.count(k) > 1}
    if dupes:
        raise ValueError(f"question_key 중복: {sorted(dupes)}")
    return questions


async def _upsert(rows: list[dict[str, Any]]) -> None:
    """question_key 충돌 시 갱신 (멱등)."""
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        for row in rows:
            stmt = insert(DiagnosticQuestion).values(**row)
            stmt = stmt.on_conflict_do_update(
                index_elements=["question_key"],
                set_={k: stmt.excluded[k] for k in _UPSERT_COLUMNS if k != "question_key"},
            )
            await session.execute(stmt)
        await session.commit()
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="진단 문항 seed 적재 (멱등)")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_SEED,
        help="seed JSON 경로 (기본: scripts/diagnostic_questions_v1.json)",
    )
    args = parser.parse_args()

    if not args.file.exists():
        raise SystemExit(f"파일 없음: {args.file}")

    questions = load_seed(args.file)
    asyncio.run(_upsert([q.to_row() for q in questions]))

    from collections import Counter

    by_level = Counter(q.level for q in questions)
    by_answer = Counter(q.correct_choice for q in questions)
    print(
        f"[diagnostic] 적재 완료 — questions={len(questions)} "
        f"(레벨 {dict(by_level)}), 정답 분포 {dict(sorted(by_answer.items()))}"
    )


if __name__ == "__main__":
    main()
