import pytest
from unittest.mock import MagicMock, patch

from ii_researcher.tool_clients.scraper.scraper import Scraper, markdown_to_text
from ii_researcher.tool_clients.scraper.beautiful_soup.beautiful_soup import (
    BeautifulSoupScraper,
)
from ii_researcher.tool_clients.scraper.pymupdf.pymupdf import PyMuPDFScraper
from ii_researcher.tool_clients.scraper.youtube.youtube import YoutubeScraper
from ii_researcher.tool_clients.scraper.tavily_extract.tavily_extract import (
    TavilyExtract,
)
from ii_researcher.tool_clients.scraper.firecrawl.firecrawl import FirecrawlScraper
from ii_researcher.tool_clients.scraper.browser.browser import BrowserScraper
from ii_researcher.tool_clients.scraper.jina.jina import JinaScraper


class TestMarkdownToText:
    def test_markdown_to_text(self):
        markdown_str = (
            "# Header\n\nThis is **bold** text with a [link](https://example.com)"
        )
        result = markdown_to_text(markdown_str)
        assert "Header" in result
        assert "This is bold text with a link" in result
        assert "https://example.com" not in result  # URLs are removed


class TestScraper:
    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        session.headers = {}
        return session

    @pytest.fixture
    def urls(self):
        return [
            "https://example.com",
            "https://example.com/doc.pdf",
            "https://arxiv.org/abs/1234.5678",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ]

    @patch("ii_researcher.tool_clients.scraper.scraper.requests.Session")
    def test_init(self, mock_session_class, urls):
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        scraper = Scraper(urls, "Mozilla/5.0", "bs")

        assert scraper.urls == urls
        assert scraper.scraper == "bs"
        mock_session.headers.update.assert_called_with({"User-Agent": "Mozilla/5.0"})

    @patch("ii_researcher.tool_clients.scraper.scraper.Scraper._check_pkg")
    @patch("ii_researcher.tool_clients.scraper.scraper.requests.Session")
    def test_init_tavily(self, mock_session_class, mock_check_pkg, urls):
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        scraper = Scraper(urls, "Mozilla/5.0", "tavily_extract")

        mock_check_pkg.assert_called_with("tavily_extract")

    @patch("ii_researcher.tool_clients.scraper.scraper.ThreadPoolExecutor")
    def test_run(self, mock_executor, urls):
        # Setup
        scraper = Scraper(urls, "Mozilla/5.0", "bs")
        scraper.extract_data_from_url = MagicMock()
        mock_extract_results = [
            {"url": urls[0], "raw_content": "content1", "title": "title1"},
            {"url": urls[1], "raw_content": "content2", "title": "title2"},
            {"url": urls[2], "raw_content": None, "title": "title3"},
            {"url": urls[3], "raw_content": "content4", "title": "title4"},
        ]
        scraper.extract_data_from_url.side_effect = mock_extract_results

        # Setup mock executor
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_executor_instance.map.return_value = mock_extract_results

        # Execute
        result = scraper.run()

        # Verify
        assert len(result) == 3  # Only entries with non-None raw_content
        assert result[0]["raw_content"] == "content1"
        assert result[1]["raw_content"] == "content2"
        assert result[2]["raw_content"] == "content4"

    @patch("ii_researcher.tool_clients.scraper.scraper.subprocess.check_call")
    @patch("importlib.util.find_spec")
    def test_check_pkg_already_installed(self, mock_find_spec, mock_check_call):
        # Test when package is already installed
        mock_find_spec.return_value = MagicMock()  # Package found
        scraper = Scraper(["https://example.com"], "Mozilla/5.0", "bs")
        scraper._check_pkg("tavily_extract")

        mock_find_spec.assert_called_with("tavily")
        mock_check_call.assert_not_called()

    @patch("ii_researcher.tool_clients.scraper.scraper.subprocess.check_call")
    @patch("importlib.util.find_spec")
    def test_check_pkg_needs_install(self, mock_find_spec, mock_check_call):
        # Test when package needs to be installed
        mock_find_spec.return_value = None  # Package not found
        scraper = Scraper(["https://example.com"], "Mozilla/5.0", "bs")
        scraper._check_pkg("tavily_extract")

        mock_find_spec.assert_called_with("tavily")
        mock_check_call.assert_called()

    @patch("ii_researcher.tool_clients.scraper.scraper.markdown_to_text")
    @patch("ii_researcher.tool_clients.scraper.scraper.clean")
    def test_extract_data_from_url_success(self, mock_clean, mock_markdown_to_text):
        # Setup
        link = "https://example.com"
        mock_session = MagicMock()
        mock_scraper = MagicMock()
        mock_scraper_instance = MagicMock()
        mock_scraper.return_value = mock_scraper_instance
        mock_scraper_instance.scrape.return_value = (
            "This is a long content with more than 100 characters to pass the length check in extract_data_from_url. It needs to be quite verbose.",
            "Title",
        )

        mock_markdown_to_text.return_value = "Converted markdown"
        mock_clean.return_value = "Cleaned content"

        # Execute
        scraper = Scraper([link], "Mozilla/5.0", "bs")
        scraper.get_scraper = MagicMock(return_value=mock_scraper)
        result = scraper.extract_data_from_url(link, mock_session)

        # Verify
        mock_scraper.assert_called_with(link, mock_session)
        mock_scraper_instance.scrape.assert_called()
        mock_markdown_to_text.assert_called_with(
            mock_scraper_instance.scrape.return_value[0]
        )
        mock_clean.assert_called()

        assert result["url"] == link
        assert result["raw_content"] == "Cleaned content"
        assert result["title"] == "Title"

    def test_extract_data_from_url_arxiv(self):
        # Test arxiv link handling
        link = "https://arxiv.org/abs/1234.5678"
        expected_link = "https://arxiv.org/html/1234.5678"
        mock_session = MagicMock()

        # Setup mock scraper
        mock_scraper = MagicMock()
        mock_scraper_instance = MagicMock()
        mock_scraper.return_value = mock_scraper_instance
        mock_scraper_instance.scrape.return_value = (
            "Long content" * 20,
            "Title",
        )  # Content > 100 chars

        # Return the mock scraper from get_scraper
        scraper = Scraper([link], "Mozilla/5.0", "bs")
        scraper.get_scraper = MagicMock(return_value=mock_scraper)

        scraper.extract_data_from_url(link, mock_session)

        # Verify arxiv URL was modified correctly
        mock_scraper.assert_called_with(expected_link, mock_session)

    def test_extract_data_from_url_content_too_short(self):
        link = "https://example.com"
        mock_session = MagicMock()

        scraper = Scraper([link], "Mozilla/5.0", "bs")
        mock_scraper = MagicMock()
        mock_scraper_instance = MagicMock()
        mock_scraper.return_value = mock_scraper_instance
        mock_scraper_instance.scrape.return_value = (
            "Short",
            "Title",
        )  # Content < 100 chars

        scraper.get_scraper = MagicMock(return_value=mock_scraper)

        result = scraper.extract_data_from_url(link, mock_session)

        assert result["url"] == link
        assert result["raw_content"] is None
        assert result["title"] == "Title"

    def test_extract_data_from_url_exception(self):
        link = "https://example.com"
        mock_session = MagicMock()

        scraper = Scraper([link], "Mozilla/5.0", "bs")
        mock_scraper = MagicMock()
        mock_scraper.return_value.scrape.side_effect = Exception("Test error")

        scraper.get_scraper = MagicMock(return_value=mock_scraper)

        result = scraper.extract_data_from_url(link, mock_session)

        assert result["url"] == link
        assert result["raw_content"] is None
        assert result["title"] == ""

    @patch("ii_researcher.tool_clients.scraper.scraper.is_pdf_url")
    def test_get_scraper_pdf(self, mock_is_pdf_url):
        # Setup mock return values
        mock_is_pdf_url.return_value = True

        scraper = Scraper(["https://example.com"], "Mozilla/5.0", "bs")

        # Test PDF by extension
        scraper_class = scraper.get_scraper("https://example.com/document.pdf")
        assert scraper_class == PyMuPDFScraper

        # Test PDF by is_pdf_url check
        scraper_class = scraper.get_scraper("https://example.com/document")
        assert scraper_class == PyMuPDFScraper
        mock_is_pdf_url.assert_called_with("https://example.com/document")

    def test_get_scraper_youtube(self):
        scraper = Scraper(["https://example.com"], "Mozilla/5.0", "bs")

        # Test different YouTube URL formats
        youtube_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
        ]

        for url in youtube_urls:
            scraper_class = scraper.get_scraper(url)
            assert scraper_class == YoutubeScraper

    def test_get_scraper_default(self):
        # Test that default scraper type is used when no special conditions are met
        scraper = Scraper(["https://example.com"], "Mozilla/5.0", "bs")
        scraper_class = scraper.get_scraper("https://example.com/page")
        assert scraper_class == BeautifulSoupScraper

        # Test with different default scraper
        scraper = Scraper(["https://example.com"], "Mozilla/5.0", "browser")
        scraper_class = scraper.get_scraper("https://example.com/page")
        assert scraper_class == BrowserScraper

        # Test with Tavily
        scraper = Scraper(["https://example.com"], "Mozilla/5.0", "tavily_extract")
        scraper_class = scraper.get_scraper("https://example.com/page")
        assert scraper_class == TavilyExtract

        # Test with Firecrawl
        scraper = Scraper(["https://example.com"], "Mozilla/5.0", "firecrawl")
        scraper_class = scraper.get_scraper("https://example.com/page")
        assert scraper_class == FirecrawlScraper

        # Test with Jina
        scraper = Scraper(["https://example.com"], "Mozilla/5.0", "jina")
        scraper_class = scraper.get_scraper("https://example.com/page")
        assert scraper_class == JinaScraper

    def test_get_scraper_invalid(self):
        scraper = Scraper(["https://example.com"], "Mozilla/5.0", "invalid_scraper")
        with pytest.raises(Exception, match="Scraper not found"):
            scraper.get_scraper("https://example.com/page")
