"""Anonymous Parallel search using the MCP Streamable HTTP transport."""

import asyncio
from datetime import timedelta
from uuid import uuid4

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from ii_researcher.config import SEARCH_QUERY_TIMEOUT

MCP_URL = "https://search.parallel.ai/mcp"
USER_AGENT = "ii-researcher/0.1.6"


async def search_parallel(query: str, max_results: int) -> list[dict[str, str]]:
    """Return the native search result shape without reading API credentials."""

    async def execute() -> list[dict[str, str]]:
        async with streamablehttp_client(
            MCP_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=timedelta(seconds=SEARCH_QUERY_TIMEOUT),
            sse_read_timeout=timedelta(seconds=SEARCH_QUERY_TIMEOUT),
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "web_search",
                    {
                        "objective": query,
                        "search_queries": [query],
                        "session_id": str(uuid4()),
                    },
                )
                if result.isError:
                    raise ValueError("Parallel MCP search failed")
                data = result.structuredContent
                if not isinstance(data, dict) or not isinstance(
                    data.get("results"), list
                ):
                    raise ValueError(
                        "Parallel MCP returned no structured search results"
                    )
                return [
                    {
                        "title": item.get("title") or "",
                        "url": item["url"],
                        "content": "\n".join(item.get("excerpts", [])),
                    }
                    for item in data["results"][:max_results]
                ]

    return await asyncio.wait_for(execute(), timeout=SEARCH_QUERY_TIMEOUT)
