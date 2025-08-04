import os
import re
import urllib.parse

import requests
from tavily import TavilyClient, MissingAPIKeyError, InvalidAPIKeyError


class SearchClient:
    """A class that provides web search capabilities using different search providers."""

    def __init__(self, query=None, max_results=10, search_provider="tavily"):
        """
        Initialize the WebSearchTool with search parameters and API keys.

        Args:
            query: The search query to execute
            max_results: Maximum number of results to return
            search_provider: The search provider to use ("serpapi" or "tavily")
        """
        self.query = query
        self.max_results = max_results
        self.search_provider = search_provider.lower()

    def _search_query_by_tavily(self, query, max_results=10):
        """Searches the query using Tavily API."""
        tavily_api_key = os.environ.get("TAVILY_API_KEY")
        try:
            client = TavilyClient(tavily_api_key)
            response = client.search(
                query=query,
                max_results=max_results,
                include_raw_content=True,
                # search_depth="advanced",
            )
            return response.get("results", [])
        except (MissingAPIKeyError, InvalidAPIKeyError) as e:
            print(f"API Key Error: {e}. Failed fetching sources from Tavily.")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}. Failed fetching sources from Tavily.")
            return []

    def _search_query_by_jina(self, query, max_results=10):
        """Searches the query using Jina AI search API."""
        jina_api_key = os.environ.get("JINA_API_KEY")
        if not jina_api_key:
            print("Error: JINA_API_KEY environment variable not set")
            return []

        url = "https://s.jina.ai/"
        params = {"q": query, "num": max_results}
        encoded_url = url + "?" + urllib.parse.urlencode(params)

        headers = {
            "Authorization": f"Bearer {jina_api_key}",
            "X-Respond-With": "no-content",
            "Accept": "application/json",
        }

        search_response = []
        try:
            response = requests.get(encoded_url, headers=headers)
            if response.status_code == 200:
                search_results = response.json()["data"]
                if search_results:
                    for result in search_results:
                        search_response.append(
                            {
                                "title": result.get("title", ""),
                                "url": result.get("url", ""),
                                "content": result.get("description", ""),
                            }
                        )
                return search_response
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []

        return search_response

    def _search_query_by_serp_api(self, query, max_results=10):
        """Searches the query using SerpAPI."""

        serpapi_api_key = os.environ.get("SERPAPI_API_KEY")

        url = "https://serpapi.com/search.json"
        params = {"q": query, "api_key": serpapi_api_key}
        encoded_url = url + "?" + urllib.parse.urlencode(params)
        search_response = []
        try:
            response = requests.get(encoded_url)
            if response.status_code == 200:
                search_results = response.json()
                if search_results:
                    results = search_results["organic_results"]
                    results_processed = 0
                    for result in results:
                        if results_processed >= max_results:
                            break
                        search_response.append(
                            {
                                "title": result["title"],
                                "url": result["link"],
                                "content": result["snippet"],
                            }
                        )
                        results_processed += 1
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources. Resulting in empty response.")
            search_response = []

        return search_response

    def search(self, query=None, max_results=None):
        """
        Execute search using configured provider or provided parameters.

        Args:
            query: The search query (overrides initialization parameter)
            max_results: Maximum number of results (overrides initialization parameter)
        """
        query = query or self.query
        max_results = max_results or self.max_results

        if not query:
            return []

        if self.search_provider == "tavily":
            return self._search_query_by_tavily(query, max_results)
        elif self.search_provider == "serpapi":
            return self._search_query_by_serp_api(query, max_results)
        elif self.search_provider == "jina":
            return self._search_query_by_jina(query, max_results)
        print(f"Error: Invalid search provider specified {self.search_provider}")
        return {}


def remove_all_line_breaks(text: str) -> str:
    """
    Remove all line breaks from text and replace them with spaces.

    Args:
        text: Input string

    Returns:
        String with line breaks replaced with spaces
    """
    return re.sub(r"(\r\n|\n|\r)", " ", text)
