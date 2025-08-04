import asyncio
import logging
from ii_researcher.reasoning.config import ConfigConstants, get_config
from ii_researcher.reasoning.tools.base import BaseTool
from ii_researcher.reasoning.tools.registry import register_tool
from ii_researcher.reasoning.tools.tool_history import ToolHistory

# Import the original tool implementation
from ii_researcher.tool_clients.scrape_client import ScrapeClient


@register_tool
class WebScraperTool(BaseTool):
    """Tool for scraping web pages."""

    name = "page_visit"
    description = (
        "Retrieves the content of a webpage by accessing the specified URL. "
        "This tool simulates a visit to the website and returns the full HTML "
        "source code of the page as a string"
    )
    argument_schema = {
        "urls": {
            "type": "list",
            "description": "The list of urls to visit. Max 3 urls.",
        }
    }
    return_type = "string"
    suffix = ConfigConstants.SEARCH_SUFFIX

    # Set to store already visited URLs
    _visited_urls = set()

    @classmethod
    def reset(cls) -> None:
        """Reset the set of visited URLs."""
        cls._visited_urls = set()

    async def execute(self, tool_history: ToolHistory = None, **kwargs) -> str:
        """Execute the web scraper."""
        urls = kwargs.get("urls", [])
        question = kwargs.get("question", "")  # Optional question context
        config = get_config()

        if not urls:
            return "No URLs provided."

        # Limit the number of URLs
        urls = urls[: config.tool.max_urls_to_visit]

        result_str = ""
        tasks = []

        for url in urls:
            # Check if the URL has already been visited
            if url in self._visited_urls:
                result_str += (
                    ConfigConstants.DUPLICATE_URL_TEMPLATE.format(url=url) + "\n"
                )
                continue

            # Add to visited URLs
            self._visited_urls.add(url)

            # Create a task for scraping the URL
            tasks.append(self._scrape_url(url, question))

        # Execute all scraping tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logging.error("Error during web scraping: %s", str(result))
                    result_str += f"Error scraping URL: {str(result)}\n"
                else:
                    result_str += result

        if tool_history is not None:
            tool_history.add_visited_urls(list(self._visited_urls))

        return result_str

    async def _scrape_url(self, url: str, question: str) -> str:
        """Scrape a single URL."""
        try:
            scrape_tool = ScrapeClient(query=question)
            result = await scrape_tool.scrape(url)

            # Remove raw content to reduce response size
            result.pop("raw_content", None)

            # Format the result
            return_str = ""
            if result.get("title"):
                return_str += f"Title: {result.get('title', '')}\n"
            return_str += f"URL: {result.get('url', '')}\n"
            return_str += f"Content: {result.get('content', '')}\n"
            return_str += "-----------------------------------\n"

            return return_str

        except (ConnectionError, TimeoutError) as e:
            logging.error("Network error while scraping URL '%s': %s", url, str(e))
            return f"Network error while scraping URL '{url}': {str(e)}\n"
        except ValueError as e:
            logging.error("Invalid URL '%s': %s", url, str(e))
            return f"Invalid URL '{url}': {str(e)}\n"
        except Exception as e:
            logging.error("Unexpected error while scraping URL '%s': %s", url, str(e))
            return f"Unexpected error while scraping URL '{url}': {str(e)}\n"
