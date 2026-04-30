import os
from unittest import TestCase
from unittest.mock import patch, MagicMock

from tavily.errors import MissingAPIKeyError, InvalidAPIKeyError
from ii_researcher.tool_clients.search_client import (
    SearchClient,
    remove_all_line_breaks,
)


class TestSearchClient(TestCase):
    def setUp(self):
        """Set up test cases"""
        self.query = "test query"
        self.max_results = 3
        self.mock_tavily_key = "test-tavily-key"
        self.mock_serp_key = "test-serp-key"
        self.mock_jina_key = "test-jina-key"
        self.mock_exa_key = "test-exa-key"

    def test_init_default_values(self):
        """Test initialization with default values"""
        client = SearchClient()
        self.assertIsNone(client.query)
        self.assertEqual(client.max_results, 10)
        self.assertEqual(client.search_provider, "tavily")

    def test_init_custom_values(self):
        """Test initialization with custom values"""
        client = SearchClient(
            query=self.query, max_results=self.max_results, search_provider="serpapi"
        )
        self.assertEqual(client.query, self.query)
        self.assertEqual(client.max_results, self.max_results)
        self.assertEqual(client.search_provider, "serpapi")

    @patch("requests.get")
    def test_jina_search(self, mock_get):
        """Test Jina search functionality"""
        # Mock response data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "title": "Test1",
                    "url": "http://test1.com",
                    "description": "Content 1",
                },
                {
                    "title": "Test2",
                    "url": "http://test2.com",
                    "description": "Content 2",
                },
            ]
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"JINA_API_KEY": self.mock_jina_key}):
            client = SearchClient(search_provider="jina")
            results = client.search(query=self.query, max_results=self.max_results)

            # Verify the results
            expected_results = [
                {"title": "Test1", "url": "http://test1.com", "content": "Content 1"},
                {"title": "Test2", "url": "http://test2.com", "content": "Content 2"},
            ]
            self.assertEqual(results, expected_results[: self.max_results])

            # Verify the API key was used in the request
            mock_get.assert_called_once()

    @patch("ii_researcher.tool_clients.search_client.TavilyClient")
    def test_tavily_search(self, mock_tavily):
        """Test Tavily search functionality"""
        # Mock response data
        mock_results = [
            {"title": "Test1", "url": "http://test1.com", "content": "Content 1"},
            {"title": "Test2", "url": "http://test2.com", "content": "Content 2"},
        ]
        mock_tavily_instance = MagicMock()
        mock_tavily_instance.search.return_value = {"results": mock_results}
        mock_tavily.return_value = mock_tavily_instance

        with patch.dict(os.environ, {"TAVILY_API_KEY": self.mock_tavily_key}):
            client = SearchClient(search_provider="tavily")
            results = client.search(query=self.query, max_results=self.max_results)

            # Verify the results
            self.assertEqual(results, mock_results)
            # Verify Tavily client was initialized with correct API key
            mock_tavily.assert_called_once_with(self.mock_tavily_key)
            mock_tavily_instance.search.assert_called_once_with(
                query=self.query,
                max_results=self.max_results,
                include_raw_content=True,
            )

    @patch("ii_researcher.tool_clients.search_client.TavilyClient")
    def test_tavily_search_missing_api_key(self, mock_tavily):
        """Test Tavily search with missing API key"""
        # Mock the client to raise MissingAPIKeyError during initialization
        mock_tavily.side_effect = MissingAPIKeyError()

        with patch.dict(os.environ, {"TAVILY_API_KEY": ""}):
            client = SearchClient(search_provider="tavily")
            # Should return empty list when API key is missing
            results = client.search(query=self.query)
            self.assertEqual(results, [])

    @patch("ii_researcher.tool_clients.search_client.TavilyClient")
    def test_tavily_search_invalid_api_key(self, mock_tavily):
        """Test Tavily search with invalid API key"""
        # Mock the client initialization to succeed but search to fail
        mock_tavily_instance = MagicMock()
        mock_tavily_instance.search.side_effect = InvalidAPIKeyError(
            "Unauthorized: missing or invalid API key."
        )
        mock_tavily.return_value = mock_tavily_instance

        with patch.dict(os.environ, {"TAVILY_API_KEY": "invalid-key"}):
            client = SearchClient(search_provider="tavily")
            # Should return empty list when API key is invalid
            results = client.search(query=self.query)
            self.assertEqual(results, [])

            # Verify the client was initialized
            mock_tavily.assert_called_once_with("invalid-key")

    @patch("requests.get")
    def test_serpapi_search(self, mock_get):
        """Test SerpAPI search functionality"""
        # Mock response data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "organic_results": [
                {"title": "Test1", "link": "http://test1.com", "snippet": "Content 1"},
                {"title": "Test2", "link": "http://test2.com", "snippet": "Content 2"},
            ]
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"SERPAPI_API_KEY": self.mock_serp_key}):
            client = SearchClient(search_provider="serpapi")
            results = client.search(query=self.query, max_results=self.max_results)

            # Verify the results
            expected_results = [
                {"title": "Test1", "url": "http://test1.com", "content": "Content 1"},
                {"title": "Test2", "url": "http://test2.com", "content": "Content 2"},
            ]
            self.assertEqual(results, expected_results[: self.max_results])

            # Verify the API key was used in the request
            mock_get.assert_called_once()
            call_args = mock_get.call_args[0][0]
            self.assertIn(f"api_key={self.mock_serp_key}", call_args)

    @patch("requests.get")
    def test_serpapi_search_error(self, mock_get):
        """Test SerpAPI search error handling"""
        mock_get.side_effect = Exception("API Error")

        with patch.dict(os.environ, {"SERPAPI_API_KEY": self.mock_serp_key}):
            client = SearchClient(search_provider="serpapi")
            results = client.search(query=self.query)
            self.assertEqual(results, [])

    def test_serpapi_search_missing_api_key(self):
        """Test SerpAPI search with missing API key"""
        with patch.dict(os.environ, {"SERPAPI_API_KEY": ""}):
            client = SearchClient(search_provider="serpapi")
            results = client.search(query=self.query)
            self.assertEqual(results, [])

    @patch("ii_researcher.tool_clients.search_client.Exa")
    def test_exa_search(self, mock_exa):
        """Test Exa search functionality with highlights returned."""
        mock_result_1 = MagicMock()
        mock_result_1.title = "Test1"
        mock_result_1.url = "http://test1.com"
        mock_result_1.highlights = ["Highlight 1a", "Highlight 1b"]
        mock_result_1.summary = None
        mock_result_1.text = "full text 1"

        mock_result_2 = MagicMock()
        mock_result_2.title = "Test2"
        mock_result_2.url = "http://test2.com"
        mock_result_2.highlights = ["Highlight 2"]
        mock_result_2.summary = None
        mock_result_2.text = "full text 2"

        mock_response = MagicMock()
        mock_response.results = [mock_result_1, mock_result_2]

        mock_exa_instance = MagicMock()
        mock_exa_instance.headers = {}
        mock_exa_instance.search_and_contents.return_value = mock_response
        mock_exa.return_value = mock_exa_instance

        with patch.dict(os.environ, {"EXA_API_KEY": self.mock_exa_key}, clear=False):
            client = SearchClient(search_provider="exa")
            results = client.search(query=self.query, max_results=self.max_results)

            expected_results = [
                {
                    "title": "Test1",
                    "url": "http://test1.com",
                    "content": "Highlight 1a ... Highlight 1b",
                },
                {
                    "title": "Test2",
                    "url": "http://test2.com",
                    "content": "Highlight 2",
                },
            ]
            self.assertEqual(results, expected_results)

            mock_exa.assert_called_once_with(api_key=self.mock_exa_key)
            self.assertEqual(
                mock_exa_instance.headers.get("x-exa-integration"), "ii-researcher"
            )
            call_kwargs = mock_exa_instance.search_and_contents.call_args.kwargs
            self.assertEqual(call_kwargs["num_results"], self.max_results)
            self.assertTrue(call_kwargs["text"])
            self.assertTrue(call_kwargs["highlights"])

    @patch("ii_researcher.tool_clients.search_client.Exa")
    def test_exa_search_content_fallback(self, mock_exa):
        """Test Exa content extraction falls back through highlights -> summary -> text."""
        # Result with no highlights, but a summary
        result_summary = MagicMock()
        result_summary.title = "SummaryOnly"
        result_summary.url = "http://summary.com"
        result_summary.highlights = []
        result_summary.summary = "summary content"
        result_summary.text = "ignored when summary present"

        # Result with only text
        result_text = MagicMock()
        result_text.title = "TextOnly"
        result_text.url = "http://text.com"
        result_text.highlights = None
        result_text.summary = None
        result_text.text = "raw text content"

        # Result with nothing
        result_empty = MagicMock()
        result_empty.title = "Empty"
        result_empty.url = "http://empty.com"
        result_empty.highlights = None
        result_empty.summary = None
        result_empty.text = None

        mock_response = MagicMock()
        mock_response.results = [result_summary, result_text, result_empty]

        mock_exa_instance = MagicMock()
        mock_exa_instance.headers = {}
        mock_exa_instance.search_and_contents.return_value = mock_response
        mock_exa.return_value = mock_exa_instance

        with patch.dict(os.environ, {"EXA_API_KEY": self.mock_exa_key}, clear=False):
            client = SearchClient(search_provider="exa")
            results = client.search(query=self.query)

            self.assertEqual(results[0]["content"], "summary content")
            self.assertEqual(results[1]["content"], "raw text content")
            self.assertEqual(results[2]["content"], "")

    @patch("ii_researcher.tool_clients.search_client.Exa")
    def test_exa_search_filters_from_env(self, mock_exa):
        """Test Exa filter env vars are passed to search_and_contents."""
        mock_response = MagicMock()
        mock_response.results = []
        mock_exa_instance = MagicMock()
        mock_exa_instance.headers = {}
        mock_exa_instance.search_and_contents.return_value = mock_response
        mock_exa.return_value = mock_exa_instance

        env = {
            "EXA_API_KEY": self.mock_exa_key,
            "EXA_SEARCH_TYPE": "neural",
            "EXA_CATEGORY": "research paper",
            "EXA_INCLUDE_DOMAINS": "arxiv.org, nature.com",
            "EXA_EXCLUDE_DOMAINS": "example.com",
            "EXA_INCLUDE_TEXT": "transformer",
            "EXA_EXCLUDE_TEXT": "advertisement",
            "EXA_START_PUBLISHED_DATE": "2024-01-01",
            "EXA_END_PUBLISHED_DATE": "2024-12-31",
        }
        with patch.dict(os.environ, env, clear=False):
            client = SearchClient(search_provider="exa")
            client.search(query=self.query)

        call_kwargs = mock_exa_instance.search_and_contents.call_args.kwargs
        self.assertEqual(call_kwargs["type"], "neural")
        self.assertEqual(call_kwargs["category"], "research paper")
        self.assertEqual(call_kwargs["include_domains"], ["arxiv.org", "nature.com"])
        self.assertEqual(call_kwargs["exclude_domains"], ["example.com"])
        self.assertEqual(call_kwargs["include_text"], ["transformer"])
        self.assertEqual(call_kwargs["exclude_text"], ["advertisement"])
        self.assertEqual(call_kwargs["start_published_date"], "2024-01-01")
        self.assertEqual(call_kwargs["end_published_date"], "2024-12-31")

    @patch("ii_researcher.tool_clients.search_client.Exa")
    def test_exa_search_missing_api_key(self, mock_exa):
        """Test Exa search returns [] and does not call SDK when EXA_API_KEY is unset."""
        with patch.dict(os.environ, {"EXA_API_KEY": ""}, clear=False):
            client = SearchClient(search_provider="exa")
            results = client.search(query=self.query)
            self.assertEqual(results, [])
            mock_exa.assert_not_called()

    @patch("ii_researcher.tool_clients.search_client.Exa")
    def test_exa_search_error(self, mock_exa):
        """Test Exa search returns [] on SDK exception."""
        mock_exa.side_effect = Exception("Boom")
        with patch.dict(os.environ, {"EXA_API_KEY": self.mock_exa_key}, clear=False):
            client = SearchClient(search_provider="exa")
            results = client.search(query=self.query)
            self.assertEqual(results, [])

    def test_invalid_search_provider(self):
        """Test invalid search provider"""
        client = SearchClient(search_provider="invalid")
        results = client.search(query=self.query)
        self.assertEqual(results, {})

    def test_empty_query(self):
        """Test empty query handling"""
        client = SearchClient()
        results = client.search(query=None)
        self.assertEqual(results, [])

    def test_remove_all_line_breaks(self):
        """Test line break removal function"""
        test_cases = [
            ("Hello\nWorld", "Hello World"),
            ("Hello\r\nWorld", "Hello World"),
            ("Hello\rWorld", "Hello World"),
            ("Hello World", "Hello World"),
            ("Hello\n\nWorld", "Hello  World"),
        ]

        for input_text, expected_output in test_cases:
            self.assertEqual(remove_all_line_breaks(input_text), expected_output)
