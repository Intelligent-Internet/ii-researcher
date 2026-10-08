import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from ii_researcher.tool_clients import parallel_search
from ii_researcher.tool_clients.search_client import SearchClient
from ii_researcher.reasoning.config import get_config
from ii_researcher.reasoning.tools.registry import get_tool
from ii_researcher.reasoning.tools.tool_history import ToolHistory


@pytest.fixture
def mcp_session(monkeypatch):
    session = SimpleNamespace(
        initialize=AsyncMock(),
        call_tool=AsyncMock(
            return_value=SimpleNamespace(
                isError=False,
                structuredContent={
                    "results": [
                        {
                            "title": "Python",
                            "url": "https://python.org",
                            "excerpts": ["First", "Second"],
                        },
                        {
                            "title": "Extra",
                            "url": "https://example.org",
                            "excerpts": [],
                        },
                    ]
                },
            )
        ),
    )

    @asynccontextmanager
    async def transport(url, headers, timeout, sse_read_timeout):
        assert url == "https://search.parallel.ai/mcp"
        assert headers == {"User-Agent": "ii-researcher/0.1.6"}
        assert timeout.total_seconds() == parallel_search.SEARCH_QUERY_TIMEOUT
        assert sse_read_timeout == timeout
        yield "read", "write", None

    @asynccontextmanager
    async def client(read, write):
        assert (read, write) == ("read", "write")
        yield session

    monkeypatch.setattr(parallel_search, "streamablehttp_client", transport)
    monkeypatch.setattr(parallel_search, "ClientSession", client)
    return session


def test_sync_provider_and_result_limit(mcp_session):
    assert SearchClient(search_provider="parallel").search("Python", 1) == [
        {"title": "Python", "url": "https://python.org", "content": "First\nSecond"}
    ]
    mcp_session.initialize.assert_awaited_once()
    name, arguments = mcp_session.call_tool.call_args.args
    assert name == "web_search"
    assert arguments["objective"] == "Python"
    assert arguments["search_queries"] == ["Python"]
    assert arguments["session_id"]
    assert SearchClient().search_provider == "tavily"


@pytest.mark.asyncio
async def test_registry_parallel_and_history(mcp_session, monkeypatch):
    config = get_config()
    monkeypatch.setattr(config.tool, "search_provider", "parallel")
    monkeypatch.setattr(config.tool, "max_search_results", 1)
    tool = get_tool("web_search")()
    tool.reset()
    history = ToolHistory()
    result = await tool.execute(history, queries=["Python"])
    assert "Title: Python" in result
    assert "https://python.org" in result
    assert "First\nSecond" in result
    assert "https://python.org" in history.get_searched_queries()
    tool.reset()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "result",
    [
        SimpleNamespace(isError=True, structuredContent={}),
        SimpleNamespace(isError=False, structuredContent=None),
    ],
)
async def test_mcp_errors_preserve_empty_search_result(mcp_session, result):
    mcp_session.call_tool.return_value = result
    assert await SearchClient("Python", search_provider="parallel").search_async() == []


@pytest.mark.asyncio
async def test_timeout_bounds_handshake(mcp_session, monkeypatch):
    monkeypatch.setattr(parallel_search, "SEARCH_QUERY_TIMEOUT", 0.02)

    async def stall():
        await asyncio.sleep(1)

    mcp_session.initialize.side_effect = stall
    with pytest.raises(TimeoutError):
        await parallel_search.search_parallel("Python", 1)
    mcp_session.call_tool.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancellation_reaches_transport(mcp_session):
    entered = asyncio.Event()
    cancelled = asyncio.Event()

    async def stall():
        entered.set()
        try:
            await asyncio.sleep(10)
        finally:
            cancelled.set()

    mcp_session.initialize.side_effect = stall
    task = asyncio.create_task(
        SearchClient("Python", search_provider="parallel").search_async()
    )
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cancelled.is_set()
