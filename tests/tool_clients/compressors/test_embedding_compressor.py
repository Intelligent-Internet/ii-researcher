# tests/tool_clients/compressors/test_embedding_compressor.py
import numpy as np
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from ii_researcher.tool_clients.compressor.embedding_compressor import (
    EmbeddingCompressor,
)


@pytest.mark.asyncio
async def test_acompress_with_relevant_chunks():
    """Test that acompress returns indices of chunks above the similarity threshold."""
    # Create the mock for OpenAIEmbeddings at module level
    with patch(
        "ii_researcher.tool_clients.compressor.embedding_compressor.OpenAIEmbeddings"
    ) as mock_embeddings_class:
        # Setup mock embeddings instance
        mock_embeddings = mock_embeddings_class.return_value
        mock_embeddings.aembed_query = AsyncMock()
        mock_embeddings.aembed_documents = AsyncMock()

        # Configure return values
        mock_embeddings.aembed_query.side_effect = [
            np.array([0.1, 0.2, 0.3]),  # query_emb
            np.array([0.2, 0.3, 0.4]),  # title_emb
        ]
        mock_embeddings.aembed_documents.return_value = np.array(
            [
                [0.9, 0.1, 0.2],  # High similarity with query
                [0.2, 0.2, 0.1],  # Low similarity
                [0.2, 0.8, 0.5],  # High similarity with title
                [0.1, 0.1, 0.1],  # Low similarity
            ]
        )

        # Create compressor
        compressor = EmbeddingCompressor(similarity_threshold=0.7)

        # Mock the similarity calculation to return known values
        def mock_cosine_similarity_batch(matrix1, matrix2):
            # Return a matrix with known similarities
            return np.array(
                [
                    [0.8, 0.3],  # Chunk 0: high with query, low with title
                    [0.2, 0.4],  # Chunk 1: low with both
                    [0.3, 0.9],  # Chunk 2: low with query, high with title
                    [0.1, 0.3],  # Chunk 3: low with both
                ]
            )

        compressor.cosine_similarity_batch = mock_cosine_similarity_batch

        # Test with sample data
        chunks = ["chunk1", "chunk2", "chunk3", "chunk4"]
        result = await compressor.acompress(
            chunks, title="test title", query="test query"
        )

        # Verify embeddings were requested
        mock_embeddings.aembed_query.assert_any_call("test query")
        mock_embeddings.aembed_query.assert_any_call("test title")
        mock_embeddings.aembed_documents.assert_called_once_with(chunks)

        # Expect chunks 0 and 2 to be returned (in order of relevance)
        # The implementation will sort by decreasing max similarity
        # Note: Our mock returns higher similarity for chunk 2 (0.9) than chunk 0 (0.8)
        assert result == [2, 0]


@pytest.mark.asyncio
async def test_acompress_with_no_relevant_chunks():
    """Test that acompress returns empty list when no chunks exceed threshold."""
    # Create compressor with mocked embeddings
    with patch(
        "ii_researcher.tool_clients.compressor.embedding_compressor.OpenAIEmbeddings"
    ) as mock_embeddings_class:
        mock_embeddings = mock_embeddings_class.return_value
        mock_embeddings.aembed_query = AsyncMock()
        mock_embeddings.aembed_documents = AsyncMock()

        mock_embeddings.aembed_query.side_effect = [
            np.array([0.1, 0.2, 0.3]),  # query_emb
            np.array([0.2, 0.3, 0.4]),  # title_emb
        ]
        mock_embeddings.aembed_documents.return_value = np.array(
            [
                [0.1, 0.1, 0.1],
                [0.2, 0.2, 0.2],
            ]
        )

        compressor = EmbeddingCompressor(similarity_threshold=0.9)

        # Mock the similarity calculation to return low similarities
        compressor.cosine_similarity_batch = MagicMock(
            return_value=np.array(
                [
                    [0.3, 0.4],  # All below threshold
                    [0.5, 0.6],
                ]
            )
        )

        # Test with sample data
        chunks = ["chunk1", "chunk2"]
        result = await compressor.acompress(
            chunks, title="test title", query="test query"
        )

        # Expect empty list since no chunks exceed threshold
        assert result == []


@pytest.mark.asyncio
async def test_acompress_sorting_by_relevance():
    """Test that acompress sorts results by decreasing relevance."""
    # Create compressor with mocked embeddings
    with patch(
        "ii_researcher.tool_clients.compressor.embedding_compressor.OpenAIEmbeddings"
    ) as mock_embeddings_class:
        mock_embeddings = mock_embeddings_class.return_value
        mock_embeddings.aembed_query = AsyncMock()
        mock_embeddings.aembed_documents = AsyncMock()

        mock_embeddings.aembed_query.side_effect = [
            np.array([0.1, 0.2, 0.3]),  # query_emb
            np.array([0.2, 0.3, 0.4]),  # title_emb
        ]
        mock_embeddings.aembed_documents.return_value = np.array(
            [
                [0.6, 0.5, 0.1],
                [0.7, 0.3, 0.2],
                [0.4, 0.8, 0.3],
                [0.9, 0.2, 0.4],
                [0.3, 0.4, 0.5],
            ]
        )

        compressor = EmbeddingCompressor(similarity_threshold=0.5)

        # Mock the similarity calculation to return specific similarities
        compressor.cosine_similarity_batch = MagicMock(
            return_value=np.array(
                [
                    [0.6, 0.5],  # max = 0.6
                    [0.7, 0.3],  # max = 0.7
                    [0.4, 0.8],  # max = 0.8
                    [0.9, 0.2],  # max = 0.9
                    [0.3, 0.4],  # max = 0.4 (below threshold)
                ]
            )
        )

        # Test with sample data
        chunks = ["chunk1", "chunk2", "chunk3", "chunk4", "chunk5"]
        result = await compressor.acompress(
            chunks, title="test title", query="test query"
        )

        # Expect indices sorted by decreasing max similarity: 3, 2, 1, 0
        assert result == [3, 2, 1, 0]


def test_cosine_similarity_batch():
    """Test the cosine_similarity_batch method directly."""
    # Patch OpenAIEmbeddings to avoid API key errors
    with patch(
        "ii_researcher.tool_clients.compressor.embedding_compressor.OpenAIEmbeddings"
    ):
        compressor = EmbeddingCompressor(similarity_threshold=0.5)

        # Test with simple vectors
        matrix1 = np.array([[1, 0, 0], [0, 1, 0]])

        matrix2 = np.array([[1, 0, 0], [0, 0, 1]])

        expected = np.array([[1, 0], [0, 0]])

        result = compressor.cosine_similarity_batch(matrix1, matrix2)
        np.testing.assert_almost_equal(result, expected)

        # Test with more complex vectors
        matrix1 = np.array([[1, 1, 0], [0, 1, 1]])

        matrix2 = np.array([[1, 0, 1]])

        # Expected similarity:
        # cos(matrix1[0], matrix2[0]) = (1*1 + 1*0 + 0*1) / (sqrt(2) * sqrt(2)) = 1/2
        # cos(matrix1[1], matrix2[0]) = (0*1 + 1*0 + 1*1) / (sqrt(2) * sqrt(2)) = 1/2
        expected = np.array([[0.5], [0.5]])

        result = compressor.cosine_similarity_batch(matrix1, matrix2)
        np.testing.assert_almost_equal(result, expected)
