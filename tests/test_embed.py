"""임베딩 유틸 단위 테스트 (OpenAI 호출 없음)."""

from scripts.embed_chunks import batched


def test_batched_splits() -> None:
    assert list(batched([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]


def test_batched_empty() -> None:
    assert list(batched([], 3)) == []


def test_batched_exact() -> None:
    assert list(batched([1, 2, 3, 4], 2)) == [[1, 2], [3, 4]]
