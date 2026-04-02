import pytest
from utils.chunker import count_tokens, safe_chunk, truncate_to_limit

MAX = 15000


def test_count_tokens_basic():
    assert count_tokens("hello world") == 2


def test_count_tokens_empty():
    assert count_tokens("") == 0


def test_truncate_no_op_when_short():
    text = "short text"
    assert truncate_to_limit(text, max_tokens=MAX) == text


def test_truncate_cuts_long_text():
    long_text = "word " * 20000  # ~20k tokens
    result = truncate_to_limit(long_text, max_tokens=MAX)
    assert count_tokens(result) == MAX


def test_safe_chunk_single_chunk():
    text = "token " * 100  # well under 15k
    chunks = safe_chunk(text, max_tokens=MAX)
    assert len(chunks) == 1


def test_safe_chunk_multiple_chunks():
    text = "token " * 40000  # ~40k tokens → 3 chunks
    chunks = safe_chunk(text, max_tokens=MAX)
    assert len(chunks) == 3
    for chunk in chunks:
        assert count_tokens(chunk) <= MAX


def test_safe_chunk_empty():
    chunks = safe_chunk("", max_tokens=MAX)
    assert chunks == []
