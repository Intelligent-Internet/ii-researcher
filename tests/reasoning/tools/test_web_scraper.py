import pytest
from unittest.mock import patch, AsyncMock

from ii_researcher.reasoning.tools.web_scraper import WebScraperTool
from ii_researcher.reasoning.tools.tool_history import ToolHistory
from ii_researcher.reasoning.config import ConfigConstants, get_config


class TestWebScraperTool:
    def setup_method(self):
        """Set up for each test."""
        # Reset the class variable before each test to ensure test isolation
        WebScraperTool.reset()
        self.web_scraper_tool = WebScraperTool()
        self.tool_history = ToolHistory()

        # Sample data for tests
        self.test_urls = ["https://example.com", "https://test.com"]
        self.test_url = "https://example.com"
        self.mock_scrape_result = {
            "title": "Example Domain",
            "url": "https://example.com",
            "content": "This domain is for use in illustrative examples.",
            "raw_content": "<html><body>This domain is for use in illustrative examples.</body></html>",
        }

    def teardown_method(self):
        """Clean up after each test."""
        WebScraperTool.reset()

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_scraper.ScrapeClient")
    async def test_execute_no_urls(self, mock_scrape_client):
        """Test execute with no URLs."""
        result = await self.web_scraper_tool.execute(urls=[])
        assert result == "No URLs provided."
        mock_scrape_client.assert_not_called()

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_scraper.ScrapeClient")
    async def test_execute_single_url(self, mock_scrape_client):
        """Test execute with a single URL."""
        # Set up mock
        mock_instance = AsyncMock()
        mock_instance.scrape.return_value = self.mock_scrape_result
        mock_scrape_client.return_value = mock_instance

        # Execute
        result = await self.web_scraper_tool.execute(urls=[self.test_url])

        # Assertions
        assert "Title: Example Domain" in result
        assert f"URL: {self.test_url}" in result
        assert "This domain is for use in illustrative examples." in result

        # Verify ScrapeClient was properly initialized and called
        mock_scrape_client.assert_called_once_with(query="")
        mock_instance.scrape.assert_called_once_with(self.test_url)

        # Verify URL was added to visited URLs
        assert self.test_url in WebScraperTool._visited_urls

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_scraper.ScrapeClient")
    async def test_execute_with_question(self, mock_scrape_client):
        """Test execute with a question parameter."""
        # Set up mock
        mock_instance = AsyncMock()
        mock_instance.scrape.return_value = self.mock_scrape_result
        mock_scrape_client.return_value = mock_instance

        # Execute with question parameter
        question = "What is an example domain?"
        result = await self.web_scraper_tool.execute(
            urls=[self.test_url], question=question
        )

        # Verify ScrapeClient was initialized with the question
        mock_scrape_client.assert_called_once_with(query=question)
        mock_instance.scrape.assert_called_once_with(self.test_url)

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_scraper.ScrapeClient")
    async def test_execute_multiple_urls(self, mock_scrape_client):
        """Test execute with multiple URLs."""
        # Set up mock
        mock_instance = AsyncMock()
        mock_instance.scrape.return_value = self.mock_scrape_result
        mock_scrape_client.return_value = mock_instance

        # Execute
        result = await self.web_scraper_tool.execute(urls=self.test_urls)

        # Verify ScrapeClient was called once for each URL
        assert mock_instance.scrape.call_count == len(self.test_urls)

        # Verify all URLs were added to visited URLs
        for url in self.test_urls:
            assert url in WebScraperTool._visited_urls

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_scraper.ScrapeClient")
    async def test_execute_max_urls_limit(self, mock_scrape_client):
        """Test execute respects the max_urls_to_visit limit."""
        # Set up mock
        mock_instance = AsyncMock()
        mock_instance.scrape.return_value = self.mock_scrape_result
        mock_scrape_client.return_value = mock_instance

        # Set up a list of URLs that exceeds the max limit
        config = get_config()
        config.tool.max_urls_to_visit = 2  # Mock the config
        excess_urls = [f"https://example{i}.com" for i in range(5)]

        # Execute
        with patch(
            "ii_researcher.reasoning.tools.web_scraper.get_config", return_value=config
        ):
            result = await self.web_scraper_tool.execute(urls=excess_urls)

        # Check that only max_urls_to_visit were processed
        assert mock_instance.scrape.call_count == 2

        # Verify only the first max_urls_to_visit were added to visited URLs
        for i in range(2):
            assert excess_urls[i] in WebScraperTool._visited_urls

        # Verify excess URLs were not processed
        for i in range(2, len(excess_urls)):
            assert excess_urls[i] not in WebScraperTool._visited_urls

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_scraper.ScrapeClient")
    async def test_execute_duplicate_url(self, mock_scrape_client):
        """Test execute with a duplicate URL."""
        # Set up mock
        mock_instance = AsyncMock()
        mock_instance.scrape.return_value = self.mock_scrape_result
        mock_scrape_client.return_value = mock_instance

        # Add a URL to the already visited set
        WebScraperTool._visited_urls.add(self.test_url)

        # Execute with the same URL
        result = await self.web_scraper_tool.execute(urls=[self.test_url])

        # Check that the duplicate message is in the result
        expected_msg = ConfigConstants.DUPLICATE_URL_TEMPLATE.format(url=self.test_url)
        assert expected_msg in result

        # Verify ScrapeClient was not called for the duplicate URL
        mock_instance.scrape.assert_not_called()

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_scraper.ScrapeClient")
    async def test_execute_with_tool_history(self, mock_scrape_client):
        """Test execute with tool_history parameter."""
        # Set up mock
        mock_instance = AsyncMock()
        mock_instance.scrape.return_value = self.mock_scrape_result
        mock_scrape_client.return_value = mock_instance

        # Execute with tool_history
        await self.web_scraper_tool.execute(
            tool_history=self.tool_history, urls=[self.test_url]
        )

        # Verify URL was added to tool_history
        assert self.test_url in self.tool_history.get_visited_urls()

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_scraper.ScrapeClient")
    async def test_execute_scrape_error(self, mock_scrape_client):
        """Test execute handles scraping errors."""
        # Set up mock to raise an exception
        mock_instance = AsyncMock()
        mock_instance.scrape.side_effect = Exception("Scraping error")
        mock_scrape_client.return_value = mock_instance

        # Execute
        result = await self.web_scraper_tool.execute(urls=[self.test_url])

        # Verify error message is in the result
        assert (
            f"Unexpected error while scraping URL '{self.test_url}': Scraping error"
            in result
        )

        # Verify URL was still added to visited URLs despite the error
        assert self.test_url in WebScraperTool._visited_urls

    def test_reset(self):
        """Test the reset class method."""
        # Add some URLs to the set
        WebScraperTool._visited_urls.add("https://example1.com")
        WebScraperTool._visited_urls.add("https://example2.com")

        # Verify URLs were added
        assert len(WebScraperTool._visited_urls) == 2

        # Reset
        WebScraperTool.reset()

        # Verify set is empty
        assert len(WebScraperTool._visited_urls) == 0
