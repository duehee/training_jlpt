"""어댑터 정규화 함수 단위 테스트 (DB 불필요)."""

from scripts.load_chunks import expand_source_pool, star_to_int, to_bool_or_none


def test_expand_source_pool_compact_csv() -> None:
    assert expand_source_pool("SRC-01,02,03,04,05,06") == [
        "SRC-01", "SRC-02", "SRC-03", "SRC-04", "SRC-05", "SRC-06",
    ]


def test_expand_source_pool_edges() -> None:
    assert expand_source_pool(None) == []
    assert expand_source_pool("SRC-02,03") == ["SRC-02", "SRC-03"]
    assert expand_source_pool("SRC-01") == ["SRC-01"]


def test_to_bool_or_none() -> None:
    assert to_bool_or_none("True") is True
    assert to_bool_or_none("False") is False
    assert to_bool_or_none("미결") is None   # 미평가 → NULL
    assert to_bool_or_none(None) is None


def test_star_to_int() -> None:
    assert star_to_int("1star") == 1
    assert star_to_int("2star") == 2
    assert star_to_int("3star") == 3