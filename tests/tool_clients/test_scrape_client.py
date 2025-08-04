import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from ii_researcher.tool_clients.scrape_client import ScrapeClient


class TestScrapeClient(unittest.TestCase):
    @patch(
        "ii_researcher.tool_clients.scrape_client.COMPRESS_EMBEDDING_MODEL",
        "test-embedding-model",
    )
    @patch(
        "ii_researcher.tool_clients.scrape_client.COMPRESS_SIMILARITY_THRESHOLD", 0.8
    )
    @patch("ii_researcher.tool_clients.scrape_client.USE_LLM_COMPRESSOR", True)
    @patch("ii_researcher.tool_clients.scrape_client.COMPRESS_MAX_INPUT_WORDS", 1000)
    @patch("ii_researcher.tool_clients.scrape_client.COMPRESS_MAX_OUTPUT_WORDS", 500)
    @patch("ii_researcher.tool_clients.scrape_client.EmbeddingCompressor")
    @patch("ii_researcher.tool_clients.scrape_client.LLMCompressor")
    @patch("ii_researcher.tool_clients.scrape_client.ContextCompressor")
    def test_init_with_defaults(
        self, mock_context_compressor, mock_llm_compressor, mock_embedding_compressor
    ):
        """Test initialization with default config (both compressors enabled)"""
        # Setup mocks
        mock_embedding_instance = MagicMock()
        mock_llm_instance = MagicMock()
        mock_embedding_compressor.return_value = mock_embedding_instance
        mock_llm_compressor.return_value = mock_llm_instance

        # Create client
        client = ScrapeClient(query="test query")

        # Verify initialization
        mock_embedding_compressor.assert_called_once_with(
            similarity_threshold=0.8, embedding_model="test-embedding-model"
        )
        mock_llm_compressor.assert_called_once()
        mock_context_compressor.assert_called_once()
        # Check that the compressors list contains both instances
        args, kwargs = mock_context_compressor.call_args
        self.assertEqual(len(kwargs["compressors"]), 2)
        self.assertIn(mock_embedding_instance, kwargs["compressors"])
        self.assertIn(mock_llm_instance, kwargs["compressors"])

    @patch("ii_researcher.tool_clients.scrape_client.COMPRESS_EMBEDDING_MODEL", "")
    @patch("ii_researcher.tool_clients.scrape_client.USE_LLM_COMPRESSOR", True)
    @patch("ii_researcher.tool_clients.scrape_client.COMPRESS_MAX_INPUT_WORDS", 1000)
    @patch("ii_researcher.tool_clients.scrape_client.COMPRESS_MAX_OUTPUT_WORDS", 500)
    @patch("ii_researcher.tool_clients.scrape_client.LLMCompressor")
    @patch("ii_researcher.tool_clients.scrape_client.ContextCompressor")
    def test_init_with_only_llm_compressor(
        self, mock_context_compressor, mock_llm_compressor
    ):
        """Test initialization with only LLM compressor enabled"""
        # Setup mocks
        mock_llm_instance = MagicMock()
        mock_llm_compressor.return_value = mock_llm_instance

        # Create client
        client = ScrapeClient(query="test query")

        # Verify initialization
        mock_llm_compressor.assert_called_once()
        mock_context_compressor.assert_called_once()
        # Check that the compressors list contains only the LLM instance
        args, kwargs = mock_context_compressor.call_args
        self.assertEqual(len(kwargs["compressors"]), 1)
        self.assertIn(mock_llm_instance, kwargs["compressors"])

    @patch(
        "ii_researcher.tool_clients.scrape_client.COMPRESS_EMBEDDING_MODEL",
        "test-embedding-model",
    )
    @patch(
        "ii_researcher.tool_clients.scrape_client.COMPRESS_SIMILARITY_THRESHOLD", 0.8
    )
    @patch("ii_researcher.tool_clients.scrape_client.USE_LLM_COMPRESSOR", False)
    @patch("ii_researcher.tool_clients.scrape_client.COMPRESS_MAX_INPUT_WORDS", 1000)
    @patch("ii_researcher.tool_clients.scrape_client.COMPRESS_MAX_OUTPUT_WORDS", 500)
    @patch("ii_researcher.tool_clients.scrape_client.EmbeddingCompressor")
    @patch("ii_researcher.tool_clients.scrape_client.ContextCompressor")
    def test_init_with_only_embedding_compressor(
        self, mock_context_compressor, mock_embedding_compressor
    ):
        """Test initialization with only embedding compressor enabled"""
        # Setup mocks
        mock_embedding_instance = MagicMock()
        mock_embedding_compressor.return_value = mock_embedding_instance

        # Create client
        client = ScrapeClient(query="test query")

        # Verify initialization
        mock_embedding_compressor.assert_called_once_with(
            similarity_threshold=0.8, embedding_model="test-embedding-model"
        )
        mock_context_compressor.assert_called_once()
        # Check that the compressors list contains only the embedding instance
        args, kwargs = mock_context_compressor.call_args
        self.assertEqual(len(kwargs["compressors"]), 1)
        self.assertIn(mock_embedding_instance, kwargs["compressors"])

    @patch("ii_researcher.tool_clients.scrape_client.COMPRESS_EMBEDDING_MODEL", "")
    @patch("ii_researcher.tool_clients.scrape_client.USE_LLM_COMPRESSOR", False)
    def test_init_with_no_compressors(self):
        """Test initialization with no compressors, which should raise ValueError"""
        with pytest.raises(ValueError, match="No compressors available"):
            ScrapeClient(query="test query")

    def test_init_with_provided_context_compressor(self):
        """Test initialization with provided context compressor"""
        mock_context_compressor = MagicMock()
        client = ScrapeClient(
            query="test query", context_compressor=mock_context_compressor
        )
        self.assertEqual(client.context_compressor, mock_context_compressor)

    def test_handle_github_link(self):
        """Test handling of GitHub links"""
        client = ScrapeClient(query="test query", context_compressor=MagicMock())

        # Test GitHub link conversion
        github_url = "https://github.com/user/repo/blob/master/file.py"
        expected_raw_url = "https://raw.githubusercontent.com/user/repo/master/file.py"
        self.assertEqual(client._handle_github_link(github_url), expected_raw_url)

        # Test non-GitHub link remains unchanged
        non_github_url = "https://example.com/page"
        self.assertEqual(client._handle_github_link(non_github_url), non_github_url)

        # Test GitHub link without blob remains unchanged
        non_blob_github_url = "https://github.com/user/repo"
        self.assertEqual(
            client._handle_github_link(non_blob_github_url), non_blob_github_url
        )

    @patch("ii_researcher.tool_clients.scrape_client.Scraper")
    def test_scrape_urls(self, mock_scraper_class):
        """Test _scrape_urls method"""
        # Setup mocks
        mock_scraper_instance = MagicMock()
        mock_scraper_instance.run.return_value = [
            {"raw_content": "test content", "title": "Test Title"}
        ]
        mock_scraper_class.return_value = mock_scraper_instance

        # Create client with mock context compressor
        client = ScrapeClient(query="test query", context_compressor=MagicMock())

        # Call _scrape_urls
        result = client._scrape_urls(["https://example.com"])

        # Verify results
        mock_scraper_class.assert_called_once()
        mock_scraper_instance.run.assert_called_once()
        self.assertEqual(
            result, [{"raw_content": "test content", "title": "Test Title"}]
        )

    @patch("ii_researcher.tool_clients.scrape_client.Scraper")
    def test_scrape_urls_error(self, mock_scraper_class):
        """Test _scrape_urls method with error"""
        # Setup mocks
        mock_scraper_instance = MagicMock()
        mock_scraper_instance.run.side_effect = Exception("Test error")
        mock_scraper_class.return_value = mock_scraper_instance

        # Create client with mock context compressor
        client = ScrapeClient(query="test query", context_compressor=MagicMock())

        # Call _scrape_urls
        result = client._scrape_urls(["https://example.com"])

        # Verify results
        mock_scraper_class.assert_called_once()
        mock_scraper_instance.run.assert_called_once()
        self.assertEqual(result, [])


# Convert the async test methods to pytest style instead of unittest
@pytest.mark.asyncio
@patch.object(ScrapeClient, "_handle_github_link")
@patch.object(ScrapeClient, "_scrape_urls")
async def test_scrape_success(mock_scrape_urls, mock_handle_github_link):
    """Test successful scrape method"""
    # Setup mocks
    mock_handle_github_link.return_value = "https://example.com"
    mock_scrape_urls.return_value = [
        {"raw_content": "test content", "title": "Test Title"}
    ]
    mock_context_compressor = AsyncMock()
    mock_context_compressor.acompress.return_value = "compressed content"

    # Create client
    client = ScrapeClient(
        query="test query", context_compressor=mock_context_compressor
    )

    # Call scrape
    result = await client.scrape("https://example.com")

    # Verify results
    mock_handle_github_link.assert_called_once_with("https://example.com")
    mock_scrape_urls.assert_called_once_with(["https://example.com"])
    mock_context_compressor.acompress.assert_called_once_with(
        "test content", title="Test Title", query="test query"
    )
    assert result == {
        "raw_content": "test content",
        "title": "Test Title",
        "content": "compressed content",
    }


@pytest.mark.asyncio
@patch.object(ScrapeClient, "_handle_github_link")
@patch.object(ScrapeClient, "_scrape_urls")
async def test_scrape_error(mock_scrape_urls, mock_handle_github_link):
    """Test scrape method with error"""
    # Setup mocks
    mock_handle_github_link.return_value = "https://example.com"
    mock_scrape_urls.side_effect = Exception("Test error")

    # Create client
    client = ScrapeClient(query="test query", context_compressor=AsyncMock())

    # Call scrape
    result = await client.scrape("https://example.com")

    # Verify results
    mock_handle_github_link.assert_called_once_with("https://example.com")
    mock_scrape_urls.assert_called_once_with(["https://example.com"])
    assert result["url"] == "https://example.com"
    assert result["raw_content"] == ""
    assert "Unable to access the content" in result["content"]


@pytest.mark.asyncio
@patch.object(ScrapeClient, "_handle_github_link")
@patch.object(ScrapeClient, "_scrape_urls")
async def test_scrape_with_missing_title(mock_scrape_urls, mock_handle_github_link):
    """Test scrape method with missing title"""
    # Setup mocks
    mock_handle_github_link.return_value = "https://example.com"
    mock_scrape_urls.return_value = [{"raw_content": "test content"}]  # No title
    mock_context_compressor = AsyncMock()
    mock_context_compressor.acompress.return_value = "compressed content"

    # Create client
    client = ScrapeClient(
        query="test query", context_compressor=mock_context_compressor
    )

    # Call scrape
    result = await client.scrape("https://example.com")

    # Verify results
    mock_context_compressor.acompress.assert_called_once_with(
        "test content",
        title="test query",  # Should fallback to query
        query="test query",
    )
    assert result["content"] == "compressed content"


if __name__ == "__main__":
    unittest.main()
