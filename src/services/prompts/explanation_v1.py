"""설명 생성 프롬프트 템플릿 (v1).

plan §2-5: 버전 접미사(_v1) — 템플릿 변경 시 캐시 키의 template_version 동반 증가.
plan §2-3: 재설명 다양성은 temperature가 아니라 `angle` 파라미터로 확보.
설명은 JSON object로 강제 ({explanation, examples[]}).
"""

from __future__ import annotations

import json
from typing import Any

from src.services.llm.base import ChatMessage

# 캐시 키에 들어가는 템플릿 버전. 이 파일의 프롬프트 변경 시 반드시 증가.
TEMPLATE_VERSION = "explanation_v1"

# 설명 응답은 JSON object로 강제 → 파싱 안정성·환각 억제.
RESPONSE_FORMAT: dict[str, Any] = {"type": "json_object"}

# angle별 설명 관점 (재설명 시 1 → 2 → 3 순환).
ANGLE_INSTRUCTIONS: dict[int, str] = {
    1: "기본 설명: 의미와 핵심 용법을 간결하게 정리하세요.",
    2: "예문 대조 중심: 비슷한 문법과의 차이를 예문으로 보여주세요.",
    3: "한국어 모국어 화자가 흔히 틀리는 포인트를 짚어 설명하세요.",
}

_SYSTEM = (
    "당신은 JLPT 문법 교사입니다. "
    "반드시 아래에 제공된 '근거 청크'에 담긴 정보만 사용해 한국어로 설명하세요. "
    "근거에 없는 내용을 지어내지 마세요. "
    '응답은 반드시 JSON 객체 하나로만 출력하세요: '
    '{"explanation": "<한국어 설명>", "examples": ["<일본어 예문 — 한국어 뜻>", ...]}'
)


def angle_for_version(explanation_version: int) -> int:
    """explanation_version(1..) → angle(1..3) 순환 매핑."""
    if explanation_version < 1:
        explanation_version = 1
    return ((explanation_version - 1) % 3) + 1


def render_context(chunks: list[dict[str, Any]]) -> str:
    """retrieved 청크들을 프롬프트용 근거 텍스트로 직렬화."""
    lines: list[str] = []
    for c in chunks:
        body = json.dumps(c.get("body", {}), ensure_ascii=False)
        lines.append(f"[{c.get('chunk_type')}] {c.get('chunk_key')}: {body}")
    return "\n".join(lines)


def build_messages(
    *,
    grammar_point_id: str,
    level: str,
    chunks: list[dict[str, Any]],
    angle: int,
) -> list[ChatMessage]:
    """설명 생성용 chat 메시지를 구성한다."""
    angle_instr = ANGLE_INSTRUCTIONS.get(angle, ANGLE_INSTRUCTIONS[1])
    context = render_context(chunks)
    user = (
        f"학습 대상 문법 포인트: {grammar_point_id} (레벨 {level})\n"
        f"설명 관점: {angle_instr}\n\n"
        f"근거 청크:\n{context}\n\n"
        "위 근거만 사용해 학습자가 이해하기 쉽게 설명하고, 예문을 포함하세요."
    )
    return [
        ChatMessage(role="system", content=_SYSTEM),
        ChatMessage(role="user", content=user),
    ]
