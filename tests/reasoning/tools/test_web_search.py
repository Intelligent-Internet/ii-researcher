import pytest
from unittest.mock import patch, MagicMock

from ii_researcher.reasoning.tools.web_search import WebSearchTool
from ii_researcher.reasoning.tools.tool_history import ToolHistory
from ii_researcher.reasoning.config import ConfigConstants, get_config


class TestWebSearchTool:
    def setup_method(self):
        """Set up for each test."""
        # Reset the class variable before each test to ensure test isolation
        WebSearchTool.reset()
        self.web_search_tool = WebSearchTool()
        self.tool_history = ToolHistory()

        # Sample data for tests
        self.test_query = "test query"
        self.test_queries = ["test query 1", "test query 2"]
        self.mock_search_results = [
            {
                "title": "Test Title 1",
                "url": "https://test1.com",
                "content": "Test content 1",
            },
            {
                "title": "Test Title 2",
                "url": "https://test2.com",
                "content": "Test content 2",
            },
        ]

    def teardown_method(self):
        """Clean up after each test."""
        WebSearchTool.reset()

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_search.SearchClient")
    async def test_execute_no_queries(self, mock_search_client):
        """Test execute with no queries."""
        result = await self.web_search_tool.execute(queries=[])
        assert result == "No search queries provided."
        mock_search_client.assert_not_called()

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_search.SearchClient")
    async def test_execute_single_query(self, mock_search_client):
        """Test execute with a single query."""
        # Set up mock
        mock_instance = MagicMock()
        mock_instance.search.return_value = self.mock_search_results
        mock_search_client.return_value = mock_instance

        # Execute
        result = await self.web_search_tool.execute(queries=[self.test_query])

        # Assertions
        assert f"Query: {self.test_query}" in result
        assert "Test Title 1" in result
        assert "https://test1.com" in result
        assert "Test content 1" in result
        assert "Test Title 2" in result

        # Verify SearchClient was properly initialized and called
        config = get_config()
        mock_search_client.assert_called_once_with(
            query=self.test_query,
            max_results=config.tool.max_search_results,
            search_provider=config.tool.search_provider,
        )
        mock_instance.search.assert_called_once()

        # Verify query was added to searched queries
        assert self.test_query in WebSearchTool._searched_queries

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_search.SearchClient")
    async def test_execute_multiple_queries(self, mock_search_client):
        """Test execute with multiple queries."""
        # Set up mock
        mock_instance = MagicMock()
        mock_instance.search.return_value = self.mock_search_results
        mock_search_client.return_value = mock_instance

        # Execute
        result = await self.web_search_tool.execute(queries=self.test_queries)

        # Assertions
        for query in self.test_queries:
            assert f"Query: {query}" in result

        # Verify SearchClient was called twice (once for each query)
        assert mock_search_client.call_count == 2

        # Verify all queries were added to searched queries
        for query in self.test_queries:
            assert query in WebSearchTool._searched_queries

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_search.SearchClient")
    async def test_execute_max_queries_limit(self, mock_search_client):
        """Test execute respects the max_search_queries limit."""
        # Set up mock
        mock_instance = MagicMock()
        mock_instance.search.return_value = self.mock_search_results
        mock_search_client.return_value = mock_instance

        # Set up a list of queries that exceeds the max limit
        config = get_config()
        max_queries = config.tool.max_search_queries
        excess_queries = ["query" + str(i) for i in range(max_queries + 3)]

        # Execute
        result = await self.web_search_tool.execute(queries=excess_queries)

        # Check that only max_queries were processed
        assert mock_search_client.call_count == max_queries

        # Verify only the first max_queries were added to searched queries
        for i in range(max_queries):
            assert excess_queries[i] in WebSearchTool._searched_queries

        # Verify excess queries were not processed
        for i in range(max_queries, len(excess_queries)):
            assert excess_queries[i] not in WebSearchTool._searched_queries

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_search.SearchClient")
    async def test_execute_duplicate_query(self, mock_search_client):
        """Test execute with a duplicate query."""
        # Set up mock
        mock_instance = MagicMock()
        mock_instance.search.return_value = self.mock_search_results
        mock_search_client.return_value = mock_instance

        # Add a query to the already searched set
        WebSearchTool._searched_queries.add(self.test_query)

        # Execute with the same query
        result = await self.web_search_tool.execute(queries=[self.test_query])

        # Check that the duplicate message is in the result
        expected_msg = ConfigConstants.DUPLICATE_QUERY_TEMPLATE.format(
            query=self.test_query
        )
        assert expected_msg in result

        # Verify SearchClient was not called for the duplicate query
        mock_search_client.assert_not_called()

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_search.SearchClient")
    async def test_execute_with_tool_history(self, mock_search_client):
        """Test execute with tool_history parameter."""
        # Set up mock
        mock_instance = MagicMock()
        mock_instance.search.return_value = self.mock_search_results
        mock_search_client.return_value = mock_instance

        # Execute with tool_history
        await self.web_search_tool.execute(
            tool_history=self.tool_history, queries=[self.test_query]
        )

        # Verify URLs were added to tool_history
        for result in self.mock_search_results:
            assert result["url"] in self.tool_history.get_searched_queries()

    @pytest.mark.asyncio
    @patch("ii_researcher.reasoning.tools.web_search.SearchClient")
    async def test_execute_search_error(self, mock_search_client):
        """Test execute handles search errors."""
        # Set up mock to raise an exception
        mock_instance = MagicMock()
        mock_instance.search.side_effect = Exception("Search error")
        mock_search_client.return_value = mock_instance

        # Execute
        result = await self.web_search_tool.execute(queries=[self.test_query])

        # Verify error message is in the result
        assert f"Error searching for '{self.test_query}': Search error" in result

        # Verify query was still added to searched queries despite the error
        assert self.test_query in WebSearchTool._searched_queries

    def test_reset(self):
        """Test the reset class method."""
        # Add some queries to the set
        WebSearchTool._searched_queries.add("query1")
        WebSearchTool._searched_queries.add("query2")

        # Verify queries were added
        assert len(WebSearchTool._searched_queries) == 2

        # Reset
        WebSearchTool.reset()

        # Verify set is empty
        assert len(WebSearchTool._searched_queries) == 0
