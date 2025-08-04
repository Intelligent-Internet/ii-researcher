import logging
from ii_researcher.reasoning.config import ConfigConstants, get_config
from ii_researcher.reasoning.tools.base import BaseTool
from ii_researcher.reasoning.tools.registry import register_tool
from ii_researcher.reasoning.tools.tool_history import ToolHistory

# Import the original tool implementation
from ii_researcher.tool_clients.search_client import SearchClient


@register_tool
class WebSearchTool(BaseTool):
    """Tool for performing web searches."""

    name = "web_search"
    description = "Performs a google web search based on your queries (think a Google search) then returns the top search results but only the title, url and a short snippet of the search results. To get the full content of the search results, you MUST use the page_visit tool."
    argument_schema = {
        "queries": {
            "type": "list",
            "description": "The list of queries to perform. Max 2 queries in style of google search.",
        }
    }
    return_type = "string"
    suffix = ConfigConstants.SEARCH_SUFFIX

    # Set to store already searched queries
    _searched_queries = set()

    @classmethod
    def reset(cls) -> None:
        """Reset the set of searched queries."""
        cls._searched_queries = set()

    async def execute(self, tool_history: ToolHistory = None, **kwargs) -> str:
        """Execute the web search."""
        queries = kwargs.get("queries", [])
        config = get_config()

        if not queries:
            return "No search queries provided."

        # Limit the number of queries
        queries = queries[: config.tool.max_search_queries]

        result_str = ""
        for query in queries:
            # Check if the query has already been searched
            if query in self._searched_queries:
                result_str += (
                    ConfigConstants.DUPLICATE_QUERY_TEMPLATE.format(query=query) + "\n"
                )
                continue

            try:
                # Add to searched queries
                self._searched_queries.add(query)

                # Perform the search
                search_tool = SearchClient(
                    query=query,
                    max_results=config.tool.max_search_results,
                    search_provider=config.tool.search_provider,
                )

                results = search_tool.search()

                # Format the results
                result_str += f"Query: {query}\n"
                for i, item in enumerate(results):
                    result_str += f"Output {i+1}:\n"
                    result_str += f"Title: {item['title']}\n"
                    result_str += f"URL: {item['url']}\n"
                    result_str += f"Snippet: {item['content']}\n"
                    result_str += "-----------------------------------\n"

                if tool_history is not None:
                    tool_history.add_searched_queries([item["url"] for item in results])

            except Exception as e:
                logging.error(
                    "Error during web search for query '%s': %s", query, str(e)
                )
                result_str += f"Error searching for '{query}': {str(e)}\n"

        return result_str
