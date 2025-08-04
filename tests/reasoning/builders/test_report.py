import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from ii_researcher.reasoning.builders.report import ReportBuilder, Subtopics
from ii_researcher.reasoning.models.trace import Trace
from ii_researcher.reasoning.tools.tool_history import ToolHistory
from ii_researcher.reasoning.config import get_report_config


class TestReportBuilder:
    @pytest.fixture
    def report_builder(self):
        """Create a ReportBuilder instance for testing."""
        with patch(
            "ii_researcher.reasoning.builders.report.OpenAI"
        ) as mock_openai, patch(
            "ii_researcher.reasoning.builders.report.AsyncOpenAI"
        ) as mock_async_openai:
            # Setup mock client
            mock_client = MagicMock()
            mock_client.chat.completions.create = MagicMock()
            mock_client.beta.chat.completions.parse = MagicMock()

            # Setup mock async client
            mock_async_client = MagicMock()
            mock_async_client.chat.completions.create = AsyncMock()
            mock_async_client.beta.chat.completions.parse = AsyncMock()

            # Configure constructors to return our mocks
            mock_openai.return_value = mock_client
            mock_async_openai.return_value = mock_async_client

            builder = ReportBuilder()
            # Replace the created clients with our mocks
            builder.client = mock_client
            builder.async_client = mock_async_client
            yield builder

    @pytest.fixture
    def mock_trace(self):
        """Create a mock Trace instance for testing."""
        trace = MagicMock(spec=Trace)
        trace.query = "Test query"
        trace.to_string.return_value = "Test trace content"
        return trace

    @pytest.fixture
    def mock_tool_history(self):
        """Create a mock ToolHistory instance for testing."""
        tool_history = MagicMock(spec=ToolHistory)
        tool_history.get_visited_urls.return_value = {
            "https://example.com",
            "https://test.com",
        }
        tool_history.get_searched_queries.return_value = {
            "search query 1",
            "search query 2",
        }
        return tool_history

    @pytest.fixture
    def mock_config(self):
        """Mock the report config."""
        config = get_report_config()
        config.generate_report_messages = MagicMock(
            return_value=[
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "User prompt"},
            ]
        )
        config.generate_introduction_messages = MagicMock(
            return_value=[
                {"role": "system", "content": "Intro system prompt"},
                {"role": "user", "content": "Intro user prompt"},
            ]
        )
        config.generate_subtopics_messages = MagicMock(
            return_value=[
                {"role": "system", "content": "Subtopics system prompt"},
                {"role": "user", "content": "Subtopics user prompt"},
            ]
        )
        config.generate_subtopic_report_messages = MagicMock(
            return_value=[
                {"role": "system", "content": "Subtopic report system prompt"},
                {"role": "user", "content": "Subtopic report user prompt"},
            ]
        )
        return config

    def test_init(self):
        """Test initialization of ReportBuilder."""
        with patch("ii_researcher.reasoning.builders.report.OpenAI"), patch(
            "ii_researcher.reasoning.builders.report.AsyncOpenAI"
        ):
            stream_event = MagicMock()
            report_builder = ReportBuilder(stream_event=stream_event)

            assert report_builder.stream_event == stream_event
            assert report_builder.config == get_report_config()
            assert hasattr(report_builder, "client")
            assert hasattr(report_builder, "async_client")

    def test_generate_report(self, mock_trace, report_builder):
        """Test generate_report method."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test report content"
        report_builder.client.chat.completions.create.return_value = mock_response

        # Call method
        report = report_builder.generate_report(mock_trace)

        # Assert result
        assert report == "Test report content"
        mock_trace.to_string.assert_called_once()
        report_builder.client.chat.completions.create.assert_called_once()

    def test_generate_report_error(self, mock_trace, report_builder):
        """Test generate_report method with error."""
        # Setup mock to raise exception
        report_builder.client.chat.completions.create.side_effect = Exception(
            "Test error"
        )

        # Call method and assert exception
        with pytest.raises(Exception):
            report_builder.generate_report(mock_trace)

    @pytest.mark.asyncio
    async def test_generate_report_stream(self, mock_trace, report_builder):
        """Test generate_report_stream method."""
        # Setup mock streaming response
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Test "
        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = "report "
        mock_chunk3 = MagicMock()
        mock_chunk3.choices = [MagicMock()]
        mock_chunk3.choices[0].delta.content = "content"

        # Configure the mock to return an async iterator
        async def mock_aiter(self):
            for chunk in [mock_chunk1, mock_chunk2, mock_chunk3]:
                yield chunk

        mock_stream = MagicMock()
        mock_stream.__aiter__ = mock_aiter
        report_builder.async_client.chat.completions.create.return_value = mock_stream

        # Mock callback
        callback = MagicMock()

        # Call method
        report = await report_builder.generate_report_stream(mock_trace, callback)

        # Assert result
        assert report == "Test report content"
        mock_trace.to_string.assert_called_once()
        report_builder.async_client.chat.completions.create.assert_called_once()
        assert callback.call_count == 3
        callback.assert_any_call("Test ")
        callback.assert_any_call("report ")
        callback.assert_any_call("content")

    @pytest.mark.asyncio
    async def test_generate_report_stream_error(self, mock_trace, report_builder):
        """Test generate_report_stream method with error."""
        # Setup mock to raise exception
        report_builder.async_client.chat.completions.create.side_effect = Exception(
            "Test error"
        )

        # Call method and assert exception
        with pytest.raises(Exception):
            await report_builder.generate_report_stream(mock_trace)

    @patch("ii_researcher.reasoning.builders.report.ReportBuilder._generate_subtopics")
    @patch(
        "ii_researcher.reasoning.builders.report.ReportBuilder._generate_introduction"
    )
    @patch(
        "ii_researcher.reasoning.builders.report.ReportBuilder._generate_subtopic_report"
    )
    @patch("ii_researcher.reasoning.builders.report.ReportBuilder._generate_references")
    def test_generate_advance_report(
        self,
        mock_gen_refs,
        mock_gen_subtopic,
        mock_gen_intro,
        mock_gen_subtopics,
        mock_trace,
        mock_tool_history,
        report_builder,
    ):
        """Test generate_advance_report method."""
        # Setup mocks
        mock_gen_subtopics.return_value = ["Topic 1", "Topic 2"]
        mock_gen_intro.return_value = "Test introduction"
        mock_gen_subtopic.side_effect = [
            "Test subtopic 1 content",
            "Test subtopic 2 content",
        ]
        mock_gen_refs.return_value = (
            "\n\n## References\n- [https://example.com](https://example.com)"
        )

        # Call method
        report = report_builder.generate_advance_report(mock_tool_history, mock_trace)

        # Assert result
        assert "Test introduction" in report
        assert "Test subtopic 1 content" in report
        assert "Test subtopic 2 content" in report
        assert "## References" in report
        mock_gen_subtopics.assert_called_once_with(mock_trace)
        mock_gen_intro.assert_called_once_with(mock_trace)
        assert mock_gen_subtopic.call_count == 2
        mock_gen_refs.assert_called_once_with(mock_tool_history)

    @patch("ii_researcher.reasoning.builders.report.ReportBuilder._generate_subtopics")
    def test_generate_advance_report_error(
        self, mock_gen_subtopics, mock_trace, mock_tool_history, report_builder
    ):
        """Test generate_advance_report method with error."""
        # Setup mock to raise exception
        mock_gen_subtopics.side_effect = Exception("Test error")

        # Call method and assert exception
        with pytest.raises(Exception):
            report_builder.generate_advance_report(mock_tool_history, mock_trace)

    @pytest.mark.asyncio
    @patch(
        "ii_researcher.reasoning.builders.report.ReportBuilder._generate_subtopics_stream"
    )
    @patch(
        "ii_researcher.reasoning.builders.report.ReportBuilder._generate_introduction_stream"
    )
    @patch(
        "ii_researcher.reasoning.builders.report.ReportBuilder._generate_subtopic_report_stream"
    )
    @patch(
        "ii_researcher.reasoning.builders.report.ReportBuilder._generate_references_stream"
    )
    async def test_generate_advance_report_stream(
        self,
        mock_gen_refs_stream,
        mock_gen_subtopic_stream,
        mock_gen_intro_stream,
        mock_gen_subtopics_stream,
        mock_trace,
        mock_tool_history,
        report_builder,
    ):
        """Test generate_advance_report_stream method."""
        # Setup mocks
        mock_gen_subtopics_stream.return_value = ["Topic 1", "Topic 2"]
        mock_gen_intro_stream.return_value = "Test introduction"
        mock_gen_subtopic_stream.side_effect = [
            "Test subtopic 1 content",
            "Test subtopic 2 content",
        ]
        mock_gen_refs_stream.return_value = (
            "\n\n## References\n- [https://example.com](https://example.com)"
        )

        # Mock callback
        callback = MagicMock()

        # Call method
        report = await report_builder.generate_advance_report_stream(
            mock_tool_history, mock_trace, callback
        )

        # Assert result
        assert "Test introduction" in report
        assert "Test subtopic 1 content" in report
        assert "Test subtopic 2 content" in report
        assert "## References" in report
        mock_gen_subtopics_stream.assert_called_once_with(mock_trace)
        mock_gen_intro_stream.assert_called_once_with(mock_trace, callback)
        assert mock_gen_subtopic_stream.call_count == 2
        mock_gen_refs_stream.assert_called_once_with(mock_tool_history, callback)

    @pytest.mark.asyncio
    @patch(
        "ii_researcher.reasoning.builders.report.ReportBuilder._generate_subtopics_stream"
    )
    async def test_generate_advance_report_stream_error(
        self, mock_gen_subtopics_stream, mock_trace, mock_tool_history, report_builder
    ):
        """Test generate_advance_report_stream method with error."""
        # Setup mock to raise exception
        mock_gen_subtopics_stream.side_effect = Exception("Test error")

        # Call method and assert exception
        with pytest.raises(Exception):
            await report_builder.generate_advance_report_stream(
                mock_tool_history, mock_trace
            )

    @pytest.mark.asyncio
    async def test_generate_introduction_stream(self, mock_trace, report_builder):
        """Test _generate_introduction_stream method."""
        # Setup mock streaming response
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "Test introduction"

        # Configure the mock to return an async iterator
        async def mock_aiter(self):
            yield mock_chunk

        mock_stream = MagicMock()
        mock_stream.__aiter__ = mock_aiter
        report_builder.async_client.chat.completions.create.return_value = mock_stream

        # Mock callback
        callback = MagicMock()

        # Call method
        intro = await report_builder._generate_introduction_stream(mock_trace, callback)

        # Assert result
        assert intro == "Test introduction"
        mock_trace.to_string.assert_called_once()
        report_builder.async_client.chat.completions.create.assert_called_once()
        callback.assert_called_once_with("Test introduction")

    @pytest.mark.asyncio
    async def test_generate_subtopics_stream(self, mock_trace, report_builder):
        """Test _generate_subtopics_stream method."""
        # Setup mock parse response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.parsed = Subtopics(
            subtopics=["Topic 1", "Topic 2"]
        )
        report_builder.async_client.beta.chat.completions.parse.return_value = (
            mock_response
        )

        # Call method
        subtopics = await report_builder._generate_subtopics_stream(mock_trace)

        # Assert result
        assert subtopics == ["Topic 1", "Topic 2"]
        mock_trace.to_string.assert_called_once()
        report_builder.async_client.beta.chat.completions.parse.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_subtopic_report_stream(self, mock_trace, report_builder):
        """Test _generate_subtopic_report_stream method."""
        # Setup mock streaming response
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = "Test subtopic content"

        # Configure the mock to return an async iterator
        async def mock_aiter(self):
            yield mock_chunk

        mock_stream = MagicMock()
        mock_stream.__aiter__ = mock_aiter
        report_builder.async_client.chat.completions.create.return_value = mock_stream

        # Mock callback
        callback = MagicMock()

        # Call method
        subtopic_content = await report_builder._generate_subtopic_report_stream(
            mock_trace,
            "Test Topic",
            "Previous content",
            ["Topic 1", "Topic 2"],
            callback,
        )

        # Assert result
        assert subtopic_content == "Test subtopic content"
        mock_trace.to_string.assert_called_once()
        report_builder.async_client.chat.completions.create.assert_called_once()
        callback.assert_called_once_with("Test subtopic content")

    @pytest.mark.asyncio
    async def test_generate_references_stream(self, mock_tool_history, report_builder):
        """Test _generate_references_stream method."""
        # Mock stream_event
        report_builder.stream_event = AsyncMock()

        # Mock callback
        callback = MagicMock()

        # Call method
        references = await report_builder._generate_references_stream(
            mock_tool_history, callback
        )

        # Assert result
        assert "## References" in references
        assert "https://example.com" in references
        assert "https://test.com" in references
        assert "search query 1" in references
        assert "search query 2" in references
        mock_tool_history.get_visited_urls.assert_called_once()
        mock_tool_history.get_searched_queries.assert_called_once()
        # Callback should be called at least once for each reference
        assert callback.call_count >= 1
        # Stream event should be called at least once
        assert report_builder.stream_event.call_count >= 1

    @pytest.mark.asyncio
    async def test_generate_stream(self, report_builder):
        """Test _generate_stream method."""
        # Setup mock streaming response
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Test "
        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = "stream "
        mock_chunk3 = MagicMock()
        mock_chunk3.choices = [MagicMock()]
        mock_chunk3.choices[0].delta.content = "content"

        # Configure the mock to return an async iterator
        async def mock_aiter(self):
            for chunk in [mock_chunk1, mock_chunk2, mock_chunk3]:
                yield chunk

        mock_stream = MagicMock()
        mock_stream.__aiter__ = mock_aiter
        report_builder.async_client.chat.completions.create.return_value = mock_stream

        # Mock callback
        callback = MagicMock()

        # Mock stream_event
        report_builder.stream_event = AsyncMock()

        # Call method
        content = await report_builder._generate_stream(
            [{"role": "user", "content": "Test message"}], callback
        )

        # Assert result
        assert content == "Test stream content"
        report_builder.async_client.chat.completions.create.assert_called_once()
        assert callback.call_count == 3
        callback.assert_any_call("Test ")
        callback.assert_any_call("stream ")
        callback.assert_any_call("content")
        assert report_builder.stream_event.call_count == 3

    def test_generate_response(self, report_builder):
        """Test _generate_response method."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response content"
        report_builder.client.chat.completions.create.return_value = mock_response

        # Call method
        response = report_builder._generate_response(
            [{"role": "user", "content": "Test message"}]
        )

        # Assert result
        assert response == "Test response content"
        report_builder.client.chat.completions.create.assert_called_once()

    def test_generate_introduction(self, mock_trace, report_builder):
        """Test _generate_introduction method."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test introduction content"
        report_builder.client.chat.completions.create.return_value = mock_response

        # Call method
        intro = report_builder._generate_introduction(mock_trace)

        # Assert result
        assert intro == "Test introduction content"
        mock_trace.to_string.assert_called_once()
        report_builder.client.chat.completions.create.assert_called_once()

    def test_generate_subtopics(self, mock_trace, report_builder):
        """Test _generate_subtopics method."""
        # Setup mock parse response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.parsed = Subtopics(
            subtopics=["Topic 1", "Topic 2"]
        )
        report_builder.client.beta.chat.completions.parse.return_value = mock_response

        # Call method
        subtopics = report_builder._generate_subtopics(mock_trace)

        # Assert result
        assert subtopics == ["Topic 1", "Topic 2"]
        mock_trace.to_string.assert_called_once()
        report_builder.client.beta.chat.completions.parse.assert_called_once()

    def test_generate_subtopic_report(self, mock_trace, report_builder):
        """Test _generate_subtopic_report method."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test subtopic report content"
        report_builder.client.chat.completions.create.return_value = mock_response

        # Call method
        subtopic_report = report_builder._generate_subtopic_report(
            mock_trace, "Test Topic", "Previous content", ["Topic 1", "Topic 2"]
        )

        # Assert result
        assert subtopic_report == "Test subtopic report content"
        mock_trace.to_string.assert_called_once()
        report_builder.client.chat.completions.create.assert_called_once()

    def test_generate_references(self, mock_tool_history, report_builder):
        """Test _generate_references method."""
        # Call method
        references = report_builder._generate_references(mock_tool_history)

        # Assert result
        assert "## References" in references
        assert "https://example.com" in references
        assert "https://test.com" in references
        assert "search query 1" in references
        assert "search query 2" in references
        mock_tool_history.get_visited_urls.assert_called_once()
        mock_tool_history.get_searched_queries.assert_called_once()
