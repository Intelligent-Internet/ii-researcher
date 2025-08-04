# tests/reasoning/test_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ii_researcher.reasoning.agent import ReasoningAgent


class MockAsyncGenerator:
    """Helper class to simulate an async generator."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index < len(self.tokens):
            token = self.tokens[self.index]
            self.index += 1
            return token
        raise StopAsyncIteration


class MockOpenAIClient:
    """Mock implementation of OpenAIClient to avoid API calls."""

    def __init__(self):
        self.responses = [
            # First turn: Ask for information
            """I'll search for information to help with your question.
```py
web_search(queries=["example query"])
```<end_code>""",
            # Second turn: Provide answer
            "Based on my research, here's the answer to your question.",
        ]
        self.response_index = 0

    def generate_completion(self, trace, instructions):
        """Mock generate_completion to return predefined responses."""
        response = self.responses[self.response_index]
        self.response_index = (self.response_index + 1) % len(self.responses)
        return response

    def generate_completion_stream(self, trace, instructions):
        """Return an async generator directly instead of a coroutine."""
        response = self.responses[self.response_index]
        self.response_index = (self.response_index + 1) % len(self.responses)

        # Split response into tokens
        tokens = [response[i : i + 5] for i in range(0, len(response), 5)]
        return MockAsyncGenerator(tokens)


@pytest.mark.asyncio
async def test_agent_with_streaming():
    """Test running the agent with streaming without making API calls."""
    # Create mock OpenAI client
    mock_openai_instance = MockOpenAIClient()
    mock_openai = MagicMock()
    mock_openai.return_value = mock_openai_instance

    # Create mock tool
    mock_tool_instance = AsyncMock()
    mock_tool_instance.execute_stream.return_value = "Mock tool response streamed"
    mock_tool_instance.suffix = "Tool suffix"
    mock_tool_class = MagicMock()
    mock_tool_class.return_value = mock_tool_instance

    # Setup patching
    with patch("ii_researcher.reasoning.agent.OpenAIClient", mock_openai), patch(
        "ii_researcher.reasoning.agent.get_config"
    ) as mock_get_config, patch(
        "ii_researcher.reasoning.agent.format_tool_descriptions"
    ), patch(
        "ii_researcher.reasoning.agent.get_all_tools"
    ) as mock_get_all_tools, patch(
        "ii_researcher.reasoning.agent.get_tool", return_value=mock_tool_class
    ):
        # Setup mock config
        mock_config = MagicMock()
        mock_config.instructions = (
            "Test instructions with {available_tools} and {current_date}"
        )
        mock_config.llm = MagicMock()
        mock_config.llm.stop_sequence = ["<end_code>"]
        mock_config.llm.get_effective_stop_sequence = MagicMock(
            return_value=["<end_code>"]
        )
        mock_get_config.return_value = mock_config

        # Setup mock tools
        mock_tools = {"web_search": mock_tool_class}
        mock_get_all_tools.return_value = mock_tools

        # Create the agent
        question = "What is an example question?"
        stream_event_mock = MagicMock()
        agent = ReasoningAgent(question=question, stream_event=stream_event_mock)

        # Create on_token callback
        on_token_mock = MagicMock()

        # Mock the report generation
        mock_report_builder = MagicMock()
        mock_report_instance = AsyncMock()

        # Create an awaitable coroutine that returns a string
        async def mock_generate_report(*args, **kwargs):
            return "Mock final report"

        mock_report_instance.generate_stream = mock_generate_report
        mock_report_builder.return_value = mock_report_instance

        # Run the agent
        with patch(
            "ii_researcher.reasoning.agent.ReportBuilder", mock_report_builder
        ), patch("ii_researcher.reasoning.agent.asyncio.sleep", return_value=None):
            result = await agent.run(on_token=on_token_mock, is_stream=True)

        # Verify the result
        assert result == "Mock final report"

        # Verify on_token was called (during streaming)
        assert on_token_mock.call_count > 0
