# tests/tool_clients/test_compressor_client.py
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from ii_researcher.tool_clients.compressor.compressor_client import (
    extract_relevant_segments,
    Passage,
)


class TestCompressorClient:
    def setup_method(self):
        """Set up test cases"""
        self.sample_passage = Passage(
            text="<#1#>This is the first segment.<#2#>This is the second segment.<#3#>This is the third segment.",
            query="Tell me about the second segment",
        )
        self.sample_code_passage = Passage(
            text="<#1#>Documentation text.<#2#>```python\ndef hello():\n    print('world')\n```<#3#>More text.",
            query="Show me code examples",
        )

    @pytest.mark.asyncio
    @patch("ii_researcher.tool_clients.compressor.compressor_client.openai.AsyncOpenAI")
    async def test_extract_relevant_segments_success(self, mock_openai):
        """Test successful extraction of segment numbers"""
        # Setup mock
        mock_client = AsyncMock()
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content='{"segment_list": "2"}'))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        mock_openai.return_value = mock_client

        # Set environment variables for test
        with patch.dict(
            os.environ,
            {
                "OPENAI_BASE_URL": "https://api.example.com",
                "OPENAI_API_KEY": "test-key",
                "FAST_LLM": "gpt-3.5-turbo",
            },
        ):
            # Execute the function
            result = await extract_relevant_segments(self.sample_passage)

            # Verify the results
            assert result == "2"

            # Verify the mock was called correctly
            mock_openai.assert_called_once_with(
                base_url="https://api.example.com",
                api_key="test-key",
                max_retries=2,
                timeout=30.0,
            )

            # Verify chat completion call
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args[1]
            assert call_args["model"] == "gpt-3.5-turbo"
            assert call_args["temperature"] == 0.0
            assert call_args["response_format"] == {"type": "json_object"}
            assert "PASSAGE:" in call_args["messages"][0]["content"]
            assert self.sample_passage["text"] in call_args["messages"][0]["content"]
            assert self.sample_passage["query"] in call_args["messages"][0]["content"]

    @pytest.mark.asyncio
    @patch("ii_researcher.tool_clients.compressor.compressor_client.openai.AsyncOpenAI")
    async def test_extract_relevant_segments_code(self, mock_openai):
        """Test extraction of code segments"""
        # Setup mock
        mock_client = AsyncMock()
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content='{"segment_list": "2-3"}'))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        mock_openai.return_value = mock_client

        # Execute the function
        with patch.dict(
            os.environ,
            {
                "OPENAI_BASE_URL": "https://api.example.com",
                "OPENAI_API_KEY": "test-key",
                "FAST_LLM": "gpt-3.5-turbo",
            },
        ):
            result = await extract_relevant_segments(self.sample_code_passage)

            # Verify the results
            assert result == "2-3"

    @pytest.mark.asyncio
    @patch("ii_researcher.tool_clients.compressor.compressor_client.openai.AsyncOpenAI")
    async def test_extract_relevant_segments_no_relevant(self, mock_openai):
        """Test when no segments are relevant"""
        # Setup mock
        mock_client = AsyncMock()
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content='{"segment_list": ""}'))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        mock_openai.return_value = mock_client

        # Execute the function
        with patch.dict(
            os.environ,
            {
                "OPENAI_BASE_URL": "https://api.example.com",
                "OPENAI_API_KEY": "test-key",
                "FAST_LLM": "gpt-3.5-turbo",
            },
        ):
            result = await extract_relevant_segments(
                Passage(
                    text="<#1#>Irrelevant text.<#2#>More irrelevant text.",
                    query="Something completely different",
                )
            )

            # Verify the results
            assert result == ""

    @pytest.mark.asyncio
    @patch("ii_researcher.tool_clients.compressor.compressor_client.openai.AsyncOpenAI")
    @patch("ii_researcher.tool_clients.compressor.compressor_client.logging.error")
    async def test_extract_relevant_segments_json_error(
        self, mock_logging, mock_openai
    ):
        """Test handling of JSON decode error"""
        # Setup mock
        mock_client = AsyncMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Invalid JSON"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        mock_openai.return_value = mock_client

        # Execute the function
        with patch.dict(
            os.environ,
            {
                "OPENAI_BASE_URL": "https://api.example.com",
                "OPENAI_API_KEY": "test-key",
                "FAST_LLM": "gpt-3.5-turbo",
            },
        ):
            result = await extract_relevant_segments(self.sample_passage)

            # Verify error handling
            assert result == ""
            mock_logging.assert_called_once()
            assert "LLM Compressor Error" in mock_logging.call_args[0][0]
