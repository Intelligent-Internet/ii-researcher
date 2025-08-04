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
