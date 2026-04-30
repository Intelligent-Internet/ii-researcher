import os
import re
import urllib.parse

import requests
from exa_py import Exa
from tavily import TavilyClient, MissingAPIKeyError, InvalidAPIKeyError


class SearchClient:
    """A class that provides web search capabilities using different search providers."""

    def __init__(self, query=None, max_results=10, search_provider="tavily"):
        """
        Initialize the WebSearchTool with search parameters and API keys.

        Args:
            query: The search query to execute
            max_results: Maximum number of results to return
            search_provider: The search provider to use ("serpapi", "tavily", "jina", or "exa")
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

    def _search_query_by_exa(self, query, max_results=10):
        """Searches the query using Exa AI search API.

        Reads optional configuration from environment variables:
            EXA_API_KEY: API key (required)
            EXA_SEARCH_TYPE: search type, one of "auto", "neural", "fast",
                "deep", "deep-lite", "deep-reasoning", "instant" (default: "auto")
            EXA_CATEGORY: category filter (e.g. "news", "research paper",
                "company", "personal site", "financial report", "people")
            EXA_INCLUDE_DOMAINS: comma-separated list of domains to include
            EXA_EXCLUDE_DOMAINS: comma-separated list of domains to exclude
            EXA_INCLUDE_TEXT: phrase that must appear in result text
            EXA_EXCLUDE_TEXT: phrase that must not appear in result text
            EXA_START_PUBLISHED_DATE: ISO 8601 lower bound for publish date
            EXA_END_PUBLISHED_DATE: ISO 8601 upper bound for publish date
        """
        exa_api_key = os.environ.get("EXA_API_KEY")
        if not exa_api_key:
            print("Error: EXA_API_KEY environment variable not set")
            return []

        try:
            client = Exa(api_key=exa_api_key)
            client.headers["x-exa-integration"] = "ii-researcher"

            kwargs = {
                "num_results": max_results,
                "type": os.environ.get("EXA_SEARCH_TYPE", "auto"),
                "text": True,
                "highlights": True,
            }
            category = os.environ.get("EXA_CATEGORY")
            if category:
                kwargs["category"] = category
            include_domains = _split_csv(os.environ.get("EXA_INCLUDE_DOMAINS"))
            if include_domains:
                kwargs["include_domains"] = include_domains
            exclude_domains = _split_csv(os.environ.get("EXA_EXCLUDE_DOMAINS"))
            if exclude_domains:
                kwargs["exclude_domains"] = exclude_domains
            include_text = os.environ.get("EXA_INCLUDE_TEXT")
            if include_text:
                kwargs["include_text"] = [include_text]
            exclude_text = os.environ.get("EXA_EXCLUDE_TEXT")
            if exclude_text:
                kwargs["exclude_text"] = [exclude_text]
            start_date = os.environ.get("EXA_START_PUBLISHED_DATE")
            if start_date:
                kwargs["start_published_date"] = start_date
            end_date = os.environ.get("EXA_END_PUBLISHED_DATE")
            if end_date:
                kwargs["end_published_date"] = end_date

            response = client.search_and_contents(query, **kwargs)

            search_response = []
            for result in response.results:
                search_response.append({
                    "title": getattr(result, "title", "") or "",
                    "url": getattr(result, "url", "") or "",
                    "content": _extract_exa_content(result),
                })
            return search_response
        except Exception as e:
            print(f"Error: {e}. Failed fetching sources from Exa.")
            return []

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
        elif self.search_provider == "exa":
            return self._search_query_by_exa(query, max_results)
        print(f"Error: Invalid search provider specified {self.search_provider}")
        return {}


def _split_csv(value):
    """Parse a comma-separated env var into a clean list, returning None if empty."""
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def _extract_exa_content(result):
    """Build a content snippet from an Exa result, falling back across content types."""
    highlights = getattr(result, "highlights", None)
    if highlights:
        return " ... ".join(highlights)
    summary = getattr(result, "summary", None)
    if summary:
        return summary
    text = getattr(result, "text", None)
    if text:
        return text
    return ""


def remove_all_line_breaks(text: str) -> str:
    """
    Remove all line breaks from text and replace them with spaces.

    Args:
        text: Input string

    Returns:
        String with line breaks replaced with spaces
    """
    return re.sub(r"(\r\n|\n|\r)", " ", text)
