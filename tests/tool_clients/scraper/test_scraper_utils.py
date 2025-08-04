import requests
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from ii_researcher.tool_clients.scraper.utils import (
    extract_title,
    clean_soup,
    get_text_from_soup,
    is_pdf_url,
)


class TestExtractTitle:
    def test_extract_title_with_title(self):
        html = "<html><head><title>Test Title</title></head><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        assert extract_title(soup) == "Test Title"

    def test_extract_title_without_title(self):
        html = "<html><head></head><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        assert extract_title(soup) == ""


class TestCleanSoup:
    def test_remove_unwanted_tags(self):
        html = """
        <html>
            <head><title>Test</title></head>
            <body>
                <script>console.log('test');</script>
                <style>.test{color:red;}</style>
                <div>Keep this content</div>
                <footer>Footer content</footer>
                <header>Header content</header>
                <nav>Navigation</nav>
                <menu>Menu items</menu>
                <sidebar>Sidebar content</sidebar>
                <svg>SVG content</svg>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        cleaned = clean_soup(soup)

        # Check that unwanted tags are removed
        assert len(cleaned.find_all("script")) == 0
        assert len(cleaned.find_all("style")) == 0
        assert len(cleaned.find_all("footer")) == 0
        assert len(cleaned.find_all("header")) == 0
        assert len(cleaned.find_all("nav")) == 0
        assert len(cleaned.find_all("menu")) == 0
        assert len(cleaned.find_all("sidebar")) == 0
        assert len(cleaned.find_all("svg")) == 0

        # Check that other content is preserved
        assert cleaned.find("div").text == "Keep this content"

    def test_remove_disallowed_classes(self):
        html = """
        <html>
            <body>
                <div class="content">Keep this</div>
                <div class="nav">Remove this</div>
                <div class="content menu">Remove this</div>
                <div class="sidebar">Remove this</div>
                <div class="footer extra">Remove this</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        cleaned = clean_soup(soup)

        # Check that content with disallowed classes is removed
        divs = cleaned.find_all("div")
        assert len(divs) == 1
        assert "content" in divs[0].get("class", [])
        assert "nav" not in [c for div in divs for c in div.get("class", [])]
        assert "menu" not in [c for div in divs for c in div.get("class", [])]
        assert "sidebar" not in [c for div in divs for c in div.get("class", [])]
        assert "footer" not in [c for div in divs for c in div.get("class", [])]


class TestGetTextFromSoup:
    def test_get_text_formatting(self):
        html = """
        <html>
            <body>
                <div>First paragraph</div>
                <div>Second   paragraph  with    spaces</div>
                <div>
                    Third paragraph
                    with line breaks
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        text = get_text_from_soup(soup)

        # Text should have newlines between paragraphs
        assert "First paragraph" in text
        assert "Second paragraph with spaces" in text
        assert "Third paragraph with line breaks" in text

        # Excessive spaces should be removed
        assert "  " not in text


class TestIsPdfUrl:
    @patch("requests.head")
    def test_pdf_url_true(self, mock_head):
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/pdf"}
        mock_head.return_value = mock_response

        assert is_pdf_url("http://example.com/document.pdf") is True
        mock_head.assert_called_once_with(
            "http://example.com/document.pdf", allow_redirects=True, timeout=5
        )

    @patch("requests.head")
    def test_pdf_url_false(self, mock_head):
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "text/html"}
        mock_head.return_value = mock_response

        assert is_pdf_url("http://example.com/page.html") is False

    @patch("requests.head")
    def test_pdf_url_exception(self, mock_head):
        mock_head.side_effect = requests.RequestException()

        assert is_pdf_url("http://example.com/broken") is False
