import unittest
from ii_researcher.reasoning.tools.tool_history import ToolHistory


class TestToolHistory(unittest.TestCase):
    def setUp(self):
        """Set up a new ToolHistory instance for each test."""
        self.tool_history = ToolHistory()

    def test_initialization(self):
        """Test that a new ToolHistory has empty sets."""
        self.assertEqual(list(self.tool_history.get_visited_urls()), [])
        self.assertEqual(list(self.tool_history.get_searched_queries()), [])

    def test_add_visited_urls(self):
        """Test adding URLs to the history."""
        # Add single URL
        self.tool_history.add_visited_urls(["https://example.com"])
        self.assertIn("https://example.com", self.tool_history.get_visited_urls())

        # Add multiple URLs
        self.tool_history.add_visited_urls(["https://test1.com", "https://test2.com"])
        self.assertIn("https://test1.com", self.tool_history.get_visited_urls())
        self.assertIn("https://test2.com", self.tool_history.get_visited_urls())

        # Add duplicate URLs
        initial_count = len(self.tool_history.get_visited_urls())
        self.tool_history.add_visited_urls(["https://example.com"])
        self.assertEqual(len(self.tool_history.get_visited_urls()), initial_count)

    def test_add_searched_queries(self):
        """Test adding search queries to the history."""
        # Add single query
        self.tool_history.add_searched_queries(["python unittest"])
        self.assertIn("python unittest", self.tool_history.get_searched_queries())

        # Add multiple queries
        self.tool_history.add_searched_queries(["data structures", "algorithms"])
        self.assertIn("data structures", self.tool_history.get_searched_queries())
        self.assertIn("algorithms", self.tool_history.get_searched_queries())

        # Add duplicate queries
        initial_count = len(self.tool_history.get_searched_queries())
        self.tool_history.add_searched_queries(["python unittest"])
        self.assertEqual(len(self.tool_history.get_searched_queries()), initial_count)

    def test_get_visited_urls(self):
        """Test retrieving visited URLs."""
        urls = ["https://example.com", "https://test.com"]
        self.tool_history.add_visited_urls(urls)
        retrieved_urls = self.tool_history.get_visited_urls()

        # Check that retrieved_urls contains all URLs from the original list
        for url in urls:
            self.assertIn(url, retrieved_urls)

    def test_get_searched_queries(self):
        """Test retrieving search queries."""
        queries = ["python tools", "testing frameworks"]
        self.tool_history.add_searched_queries(queries)
        retrieved_queries = self.tool_history.get_searched_queries()

        # Check that retrieved_queries contains all queries from the original list
        for query in queries:
            self.assertIn(query, retrieved_queries)


if __name__ == "__main__":
    unittest.main()
