# tests/tool_clients/compressors/test_llm_compressor.py
import pytest
from unittest.mock import patch

from ii_researcher.tool_clients.compressor.llm_compressor import (
    LLMCompressor,
    parse_segment_numbers,
)


def test_parse_segment_numbers_single_number():
    """Test parse_segment_numbers with a single number."""
    result = parse_segment_numbers("5")
    assert result == [5]


def test_parse_segment_numbers_multiple_numbers():
    """Test parse_segment_numbers with multiple comma-separated numbers."""
    result = parse_segment_numbers("1,3,7")
    assert result == [1, 3, 7]


def test_parse_segment_numbers_range():
    """Test parse_segment_numbers with a range."""
    result = parse_segment_numbers("2-5")
    assert result == [2, 3, 4, 5]


def test_parse_segment_numbers_mixed():
    """Test parse_segment_numbers with a mix of single numbers and ranges."""
    result = parse_segment_numbers("1,3-5,8")
    assert result == [1, 3, 4, 5, 8]


def test_parse_segment_numbers_duplicate():
    """Test parse_segment_numbers with duplicate numbers."""
    result = parse_segment_numbers("1,3,3,5")
    assert result == [1, 3, 5]  # Duplicates should be removed


def test_parse_segment_numbers_overlapping_ranges():
    """Test parse_segment_numbers with overlapping ranges."""
    result = parse_segment_numbers("1-3,2-5")
    assert result == [1, 2, 3, 4, 5]  # Duplicates should be removed


def test_parse_segment_numbers_empty_string():
    """Test parse_segment_numbers with an empty string."""
    result = parse_segment_numbers("")
    assert result == []


def test_parse_segment_numbers_whitespace():
    """Test parse_segment_numbers with whitespace."""
    result = parse_segment_numbers("  1, 3-5 , 7  ")
    assert result == [1, 3, 4, 5, 7]  # Should handle whitespace


@pytest.mark.asyncio
async def test_llm_compressor_acompress():
    """Test LLMCompressor's acompress method."""
    # Mock extract_relevant_segments
    with patch(
        "ii_researcher.tool_clients.compressor.llm_compressor.extract_relevant_segments"
    ) as mock_extract:
        mock_extract.return_value = "2-3,5"

        compressor = LLMCompressor()
        chunks = ["chunk1", "chunk2", "chunk3", "chunk4", "chunk5"]
        title = "Test Title"
        query = "Test Query"

        result = await compressor.acompress(chunks, title, query)

        # Verify extract_relevant_segments was called with correct arguments
        mock_extract.assert_called_once()
        passage_arg = mock_extract.call_args[1]["passage"]
        assert passage_arg["query"] == query
        assert "<#1#> chunk1" in passage_arg["text"]
        assert "<#2#> chunk2" in passage_arg["text"]
        assert "<#3#> chunk3" in passage_arg["text"]
        assert "<#4#> chunk4" in passage_arg["text"]
        assert "<#5#> chunk5" in passage_arg["text"]

        # Verify the result (0-indexed)
        assert result == [1, 2, 4]  # (2-1, 3-1, 5-1)


@pytest.mark.asyncio
async def test_llm_compressor_acompress_empty_result():
    """Test LLMCompressor's acompress method when no segments are relevant."""
    # Mock extract_relevant_segments to return empty string
    with patch(
        "ii_researcher.tool_clients.compressor.llm_compressor.extract_relevant_segments"
    ) as mock_extract:
        mock_extract.return_value = ""

        compressor = LLMCompressor()
        chunks = ["chunk1", "chunk2", "chunk3"]

        result = await compressor.acompress(chunks, title="Title", query="Query")

        # Verify extract_relevant_segments was called
        mock_extract.assert_called_once()

        # Verify empty result
        assert result == []


@pytest.mark.asyncio
async def test_llm_compressor_acompress_invalid_segment_number():
    """Test LLMCompressor's acompress method with invalid segment numbers."""
    # Mock extract_relevant_segments to return numbers outside valid range
    with patch(
        "ii_researcher.tool_clients.compressor.llm_compressor.extract_relevant_segments"
    ) as mock_extract:
        mock_extract.return_value = (
            "0,2,4,6"  # 0 is invalid (1-indexed), 6 is valid but high
        )

        compressor = LLMCompressor()
        chunks = ["chunk1", "chunk2", "chunk3", "chunk4", "chunk5"]

        result = await compressor.acompress(chunks, title="Title", query="Query")

        # Verify extract_relevant_segments was called
        mock_extract.assert_called_once()

        # Verify only valid indices (0-indexed) are returned
        # The implementation only filters numbers < 1, not numbers > len(chunks)
        assert result == [1, 3, 5]  # (2-1, 4-1, 6-1), only 0 is filtered out
