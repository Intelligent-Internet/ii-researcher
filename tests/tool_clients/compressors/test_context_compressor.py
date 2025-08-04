from typing import List
from unittest.mock import AsyncMock

import pytest

from ii_researcher.tool_clients.compressor.base import Compressor
from ii_researcher.tool_clients.compressor.context_compressor import ContextCompressor


class MockCompressor(Compressor):
    """Mock implementation of Compressor for testing"""

    def __init__(self, return_indices: List[int]):
        self.return_indices = return_indices
        self.acompress = AsyncMock(return_value=return_indices)

    async def acompress(
        self, context: str, title: str = "", query: str = ""
    ) -> List[int]:
        """Implement the abstract method from the base class"""
        return self.acompress(context=context, title=title, query=query)


@pytest.fixture
def sample_text():
    """Return a sample text with multiple paragraphs"""
    return """
    This is the first paragraph of the sample text. 
    
    This is the second paragraph of the sample text.
    
    This is the third paragraph of the sample text.
    
    This is the fourth paragraph of the sample text.
    
    This is the fifth paragraph of the sample text. 
    
    This is the sixth paragraph of the sample text.

    This is the seventh paragraph of the sample text.

    This is the eighth paragraph of the sample text.
    """


@pytest.mark.asyncio
async def test_acompress_intersection_scenario(sample_text):
    """
    Test ContextCompressor.acompress when the intersection of selected chunks exceeds max_output_words.
    In this case, it should select chunks from the intersection based on the first compressor's ordering.
    """

    # Both compressors agree on indices 0, 1, 2 but in different orders
    compressor1 = MockCompressor([0, 1, 2, 3, 4])
    compressor2 = MockCompressor([2, 0, 1, 5, 6])

    # Set max_output_words to a small value to ensure intersection exceeds it
    context_compressor_intersection_scenario = ContextCompressor(
        compressors=[compressor1, compressor2],
        max_output_words=19,  # Small enough that intersection (chunks 0,1,2) will exceed it (9 for each chunk)
        max_input_words=1000,
        chunk_size=50,  # Small chunk size to ensure multiple chunks
        chunk_overlap=0,
    )

    result = await context_compressor_intersection_scenario.acompress(
        context=sample_text, title="Sample Text", query="relevant information"
    )

    # Verify the result is a string
    assert isinstance(result, str)

    # The result should contain some content from the chunks
    assert len(result) > 0

    # Since max_output_words is small, we should get fewer chunks than the intersection (0,1,2)
    # Check it contains content from the beginning of the text (assuming first chunk is selected)
    assert "first paragraph" in result
    assert "second paragraph" in result
    assert "third paragraph" not in result

    # Compressor's acompress method should have been called
    assert context_compressor_intersection_scenario.compressors[0].acompress.called
    assert context_compressor_intersection_scenario.compressors[1].acompress.called


@pytest.mark.asyncio
async def test_acompress_union_scenario(sample_text):
    """
    Test ContextCompressor.acompress when the intersection fits within max_output_words
    but the union exceeds it. It should include all intersection chunks and some
    union-intersection chunks based on their average ranking.
    """
    # Compressors have partial overlap in their selections
    compressor1 = MockCompressor([0, 1, 3, 5])
    compressor2 = MockCompressor([0, 2, 4, 6])

    # Set max_output_words so intersection is under limit but union exceeds it
    context_compressor_union_scenario = ContextCompressor(
        compressors=[compressor1, compressor2],
        max_output_words=19,  # Between intersection and union word counts
        max_input_words=1000,
        chunk_size=50,
        chunk_overlap=0,
    )

    result = await context_compressor_union_scenario.acompress(
        context=sample_text, title="Sample Text", query="relevant information"
    )

    # Verify the result is a string
    assert isinstance(result, str)

    # The result should contain some content from the chunks
    assert len(result) > 0

    # Should contain content from the intersection (chunk 0) and first chunk of union (chunk 1)
    assert "first paragraph" in result
    assert "second paragraph" in result
    assert "third paragraph" not in result

    # Compressor's acompress method should have been called
    assert context_compressor_union_scenario.compressors[0].acompress.called
    assert context_compressor_union_scenario.compressors[1].acompress.called


@pytest.mark.asyncio
async def test_acompress_small_union_scenario(sample_text):
    """
    Test ContextCompressor.acompress when the union fits within max_output_words.
    It should include all chunks from the union.
    """
    # Compressors select a small number of chunks
    compressor1 = MockCompressor([0, 2])
    compressor2 = MockCompressor([1, 3])

    # Set max_output_words large enough to include all union chunks
    context_compressor_small_union_scenario = ContextCompressor(
        compressors=[compressor1, compressor2],
        max_output_words=10000,  # Large enough to include all union chunks
        max_input_words=10000,
        chunk_size=50,
        chunk_overlap=0,
    )

    result = await context_compressor_small_union_scenario.acompress(
        context=sample_text, title="Sample Text", query="relevant information"
    )

    # Verify the result is a string
    assert isinstance(result, str)

    # The result should contain some content from the chunks
    assert len(result) > 0

    # Should contain content from multiple chunks in the union
    assert "first paragraph" in result
    assert "second paragraph" in result
    assert "third paragraph" in result
    assert "fourth paragraph" in result
    assert "fifth paragraph" not in result

    # Compressor's acompress method should have been called
    assert context_compressor_small_union_scenario.compressors[0].acompress.called
    assert context_compressor_small_union_scenario.compressors[1].acompress.called


@pytest.mark.asyncio
async def test_acompress_empty_input():
    """Test ContextCompressor.acompress with empty input"""
    compressor1 = MockCompressor([])
    compressor2 = MockCompressor([])

    context_compressor = ContextCompressor(
        compressors=[compressor1, compressor2],
        max_output_words=100,
        max_input_words=1000,
        chunk_size=100,
        chunk_overlap=0,
    )

    result = await context_compressor.acompress(
        context="", title="Empty Text", query="relevant information"
    )

    # Result should be an empty string since there are no chunks
    assert result == ""


@pytest.mark.asyncio
async def test_acompress_single_chunk():
    """Test ContextCompressor.acompress with input that produces a single chunk"""
    compressor1 = MockCompressor([0])
    compressor2 = MockCompressor([0])

    context_compressor = ContextCompressor(
        compressors=[compressor1, compressor2],
        max_output_words=100,
        max_input_words=1000,
        chunk_size=1000,  # Large chunk size to ensure a single chunk
        chunk_overlap=0,
    )

    short_text = "This is a short piece of text that will fit in a single chunk."

    result = await context_compressor.acompress(
        context=short_text, title="Short Text", query="relevant information"
    )

    # Result should contain the short text
    assert short_text in result


@pytest.mark.asyncio
async def test_acompress_disagreeing_compressors(sample_text):
    """
    Test ContextCompressor.acompress when compressors completely disagree
    (no intersection)
    """
    compressor1 = MockCompressor([0, 1, 2])
    compressor2 = MockCompressor([3, 4, 5])

    context_compressor = ContextCompressor(
        compressors=[compressor1, compressor2],
        max_output_words=18,
        max_input_words=1000,
        chunk_size=50,
        chunk_overlap=0,
    )

    result = await context_compressor.acompress(
        context=sample_text,
        title="Disagreeing Compressors",
        query="relevant information",
    )

    # Result should not be empty
    assert result != ""

    # Should prioritize by rank
    assert "first paragraph" in result
    assert "second paragraph" not in result
    assert "third paragraph" not in result
    assert "fourth paragraph" in result
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_acompress_truncates_input():
    """
    Test that ContextCompressor.acompress truncates input to max_input_words
    """
    compressor1 = MockCompressor([0])

    small_max_input_words = 7

    context_compressor = ContextCompressor(
        compressors=[compressor1],
        max_output_words=100,
        max_input_words=small_max_input_words,
        chunk_size=50,
        chunk_overlap=0,
    )

    long_text = "This is a " + "word " * 20 + "with many words."

    result = await context_compressor.acompress(
        context=long_text, title="Long Text", query="relevant information"
    )

    # Result should only contain a truncated version of the input
    # (specifically the first max_input_words words)
    words_in_result = result.split()
    assert len(words_in_result) <= small_max_input_words
