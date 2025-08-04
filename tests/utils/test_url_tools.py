import pytest
from ii_researcher.utils.url_tools import (
    normalize_url,
    get_unvisited_urls,
    extract_domain,
)


class TestNormalizeUrl:
    def test_empty_url(self):
        with pytest.raises(ValueError, match="Empty URL"):
            normalize_url("")
        with pytest.raises(ValueError, match="Empty URL"):
            normalize_url("   ")

    def test_add_protocol(self):
        assert normalize_url("example.com") == "https://example.com/"
        assert normalize_url("http://example.com") == "http://example.com/"

    def test_normalize_hostname(self):
        assert normalize_url("WWW.EXAMPLE.COM") == "https://example.com/"
        assert normalize_url("www.example.com") == "https://example.com/"
        assert normalize_url("https://www.EXAMPLE.com") == "https://example.com/"

    def test_normalize_path(self):
        assert (
            normalize_url("example.com/path//to///page")
            == "https://example.com/path/to/page"
        )
        assert normalize_url("example.com/path/") == "https://example.com/path/"
        assert (
            normalize_url("example.com/path%20with%20spaces")
            == "https://example.com/path with spaces"
        )

    def test_debug_mode(self):
        # Test that debug mode doesn't affect the output
        normal = normalize_url("example.com/path?a=1#section")
        debug = normalize_url("example.com/path?a=1#section", debug=True)
        assert normal == debug


class TestGetUnvisitedUrls:
    def test_empty_inputs(self):
        assert get_unvisited_urls({}, []) == []
        assert get_unvisited_urls({"url": "data"}, []) == ["data"]
        assert get_unvisited_urls({}, ["url"]) == []

    def test_filter_visited_urls(self):
        all_urls = {
            "http://example1.com": {"data": 1},
            "http://example2.com": {"data": 2},
            "http://example3.com": {"data": 3},
        }
        visited_urls = ["http://example1.com", "http://example3.com"]
        result = get_unvisited_urls(all_urls, visited_urls)
        assert len(result) == 1
        assert result[0] == {"data": 2}

    def test_all_urls_visited(self):
        all_urls = {
            "http://example1.com": {"data": 1},
            "http://example2.com": {"data": 2},
        }
        visited_urls = ["http://example1.com", "http://example2.com"]
        assert get_unvisited_urls(all_urls, visited_urls) == []

    def test_no_urls_visited(self):
        all_urls = {
            "http://example1.com": {"data": 1},
            "http://example2.com": {"data": 2},
        }
        visited_urls = []
        result = get_unvisited_urls(all_urls, visited_urls)
        assert len(result) == 2
        assert {"data": 1} in result
        assert {"data": 2} in result


class TestExtractDomain:
    def test_basic_domains(self):
        assert extract_domain("https://example.com") == "example.com"
        assert extract_domain("http://subdomain.example.com") == "subdomain.example.com"
        assert extract_domain("https://example.com:8080") == "example.com:8080"

    def test_with_paths_and_parameters(self):
        assert extract_domain("https://example.com/path") == "example.com"
        assert extract_domain("https://example.com/path?param=value") == "example.com"
        assert extract_domain("https://example.com#fragment") == "example.com"

    def test_with_authentication(self):
        assert (
            extract_domain("https://user:pass@example.com") == "user:pass@example.com"
        )

    def test_empty_domain(self):
        assert extract_domain("https://") == ""
