"""캐시 키 전략 단위 테스트 (DB 불필요)."""

from src.shared.cache.base import make_cache_key, make_prompt_hash


def test_prompt_hash_deterministic() -> None:
    payload = {"task": "explanation", "grammar_point_id": "grammar_n5_001", "angle": 1}
    assert make_prompt_hash(payload) == make_prompt_hash(payload)


def test_prompt_hash_key_order_independent() -> None:
    a = {"task": "explanation", "angle": 1, "level": "N5"}
    b = {"level": "N5", "angle": 1, "task": "explanation"}
    assert make_prompt_hash(a) == make_prompt_hash(b)


def test_prompt_hash_angle_changes_hash() -> None:
    base = {"task": "explanation", "grammar_point_id": "grammar_n5_001"}
    assert make_prompt_hash({**base, "angle": 1}) != make_prompt_hash(
        {**base, "angle": 2}
    )


def test_prompt_hash_chunk_set_changes_hash() -> None:
    base = {"task": "explanation", "angle": 1}
    h1 = make_prompt_hash({**base, "chunk_keys": ["grammar_n5_001"]})
    h2 = make_prompt_hash({**base, "chunk_keys": ["grammar_n5_001", "compare_n5_001_002"]})
    assert h1 != h2


def test_prompt_hash_is_64_hex() -> None:
    h = make_prompt_hash({"x": 1})
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_cache_key_format_and_length() -> None:
    h = make_prompt_hash({"x": 1})
    key = make_cache_key("gpt-4o-mini", h)
    assert key == f"gpt-4o-mini:{h}"
    assert len(key) <= 255
