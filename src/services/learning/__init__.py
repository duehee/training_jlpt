"""학습 루프 노드 패키지 (설명 생성).

청크 검색(retrieval)은 content 도메인으로 이관됨 (세션 8 Step 5b).
"""

from __future__ import annotations

from src.services.learning.explanation import (
    ExplanationResult,
    generate_explanation,
    generate_explanation_from_chunks,
)

__all__ = [
    "ExplanationResult",
    "generate_explanation",
    "generate_explanation_from_chunks",
]
