# tests/reasoning/clients/test_openai_client.py
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from ii_researcher.reasoning.clients.openai_client import OpenAIClient
from ii_researcher.reasoning.models.trace import Trace, Turn
from ii_researcher.reasoning.models.output import ModelOutput


class TestOpenAIClient(unittest.TestCase):
    @patch("ii_researcher.reasoning.clients.openai_client.get_config")
    @patch("ii_researcher.reasoning.clients.openai_client.OpenAI")
    @patch("ii_researcher.reasoning.clients.openai_client.AsyncOpenAI")
    def setUp(self, mock_async_openai, mock_openai, mock_get_config):
        # Setup mock config
        self.mock_config = MagicMock()
        self.mock_config.llm.api_key = "test-api-key"
        self.mock_config.llm.base_url = "https://test-url.com/v1"
        self.mock_config.llm.model = "test-model"
        self.mock_config.llm.temperature = 0.2
        self.mock_config.llm.top_p = 0.95
        self.mock_config.llm.presence_penalty = 0.0
        self.mock_config.llm.stop_sequence = ["<end_code>"]
        self.mock_config.system_prompt = (
            "Test system prompt {available_tools} {current_date}"
        )

        mock_get_config.return_value = self.mock_config

        # Setup client mocks
        self.mock_client = MagicMock()
        self.mock_async_client = AsyncMock()
        mock_openai.return_value = self.mock_client
        mock_async_openai.return_value = self.mock_async_client

        # Create client
        self.client = OpenAIClient()

    @patch("ii_researcher.reasoning.clients.openai_client.format_tool_descriptions")
    def test_get_messages(self, mock_format_tool_descriptions):
        """Test _get_messages method constructs the messages correctly."""
        # Setup
        mock_format_tool_descriptions.return_value = "Tool descriptions"
        trace = Trace(query="Test query", turns=[])

        # Test without instructions
        messages = self.client._get_messages(trace)

        # Verify
        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert "Tool descriptions" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Test query"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == trace.to_string()
        assert messages[2]["prefix"] is True

        # Test with instructions
        messages = self.client._get_messages(trace, "Test instructions")
        assert messages[2]["content"] == trace.to_string("Test instructions")

    @patch.object(OpenAIClient, "_get_messages")
    def test_generate_completion(self, mock_get_messages):
        """Test generate_completion method."""
        # Setup
        mock_get_messages.return_value = [{"role": "user", "content": "test"}]

        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test completion"
        self.mock_client.chat.completions.create.return_value = mock_response

        # Test
        trace = Trace(query="Test query", turns=[])
        result = self.client.generate_completion(trace)

        # Verify
        mock_get_messages.assert_called_once_with(trace, None)
        self.mock_client.chat.completions.create.assert_called_once_with(
            model=self.mock_config.llm.model,
            messages=[{"role": "user", "content": "test"}],
            temperature=self.mock_config.llm.temperature,
            top_p=self.mock_config.llm.top_p,
            presence_penalty=self.mock_config.llm.presence_penalty,
            stop=self.mock_config.llm.stop_sequence,
        )
        assert result == "Test completion"

    @patch.object(OpenAIClient, "_get_messages")
    def test_generate_completion_with_instructions(self, mock_get_messages):
        """Test generate_completion method with instructions."""
        # Setup
        mock_get_messages.return_value = [{"role": "user", "content": "test"}]

        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test completion with instructions"
        self.mock_client.chat.completions.create.return_value = mock_response

        # Test
        trace = Trace(query="Test query", turns=[])
        result = self.client.generate_completion(trace, "Test instructions")

        # Verify
        mock_get_messages.assert_called_once_with(trace, "Test instructions")
        assert result == "Test completion with instructions"

    @patch.object(OpenAIClient, "_get_messages")
    def test_generate_completion_error(self, mock_get_messages):
        """Test generate_completion method with error."""
        # Setup
        mock_get_messages.return_value = [{"role": "user", "content": "test"}]
        self.mock_client.chat.completions.create.side_effect = Exception("Test error")

        # Test
        trace = Trace(query="Test query", turns=[])

        # Verify
        with self.assertRaises(Exception):
            self.client.generate_completion(trace)


# Separate class for async tests
class TestOpenAIClientAsync(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Setup mock config
        self.mock_config = MagicMock()
        self.mock_config.llm.api_key = "test-api-key"
        self.mock_config.llm.base_url = "https://test-url.com/v1"
        self.mock_config.llm.model = "test-model"
        self.mock_config.llm.temperature = 0.2
        self.mock_config.llm.top_p = 0.95
        self.mock_config.llm.presence_penalty = 0.0
        self.mock_config.llm.stop_sequence = ["<end_code>"]
        self.mock_config.system_prompt = (
            "Test system prompt {available_tools} {current_date}"
        )

        # Setup patches
        self.get_config_patcher = patch(
            "ii_researcher.reasoning.clients.openai_client.get_config"
        )
        self.openai_patcher = patch(
            "ii_researcher.reasoning.clients.openai_client.OpenAI"
        )
        self.async_openai_patcher = patch(
            "ii_researcher.reasoning.clients.openai_client.AsyncOpenAI"
        )

        # Start patches
        self.mock_get_config = self.get_config_patcher.start()
        self.mock_openai = self.openai_patcher.start()
        self.mock_async_openai = self.async_openai_patcher.start()

        self.mock_get_config.return_value = self.mock_config

        # Setup client mocks
        self.mock_client = MagicMock()
        self.mock_async_client = AsyncMock()
        self.mock_openai.return_value = self.mock_client
        self.mock_async_openai.return_value = self.mock_async_client

        # Create client
        self.client = OpenAIClient()

        # Mock _get_messages
        self.get_messages_patcher = patch.object(OpenAIClient, "_get_messages")
        self.mock_get_messages = self.get_messages_patcher.start()
        self.mock_get_messages.return_value = [{"role": "user", "content": "test"}]

    async def asyncTearDown(self):
        # Stop patches
        self.get_config_patcher.stop()
        self.openai_patcher.stop()
        self.async_openai_patcher.stop()
        self.get_messages_patcher.stop()

    async def test_generate_completion_stream(self):
        """Test generate_completion_stream method."""
        # Setup mock stream response
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Test "

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = "stream"

        # Configure AsyncMock to return an async iterator
        self.mock_async_client.chat.completions.create.return_value.__aiter__.return_value = [
            chunk1,
            chunk2,
        ]

        # Test
        trace = Trace(query="Test query", turns=[])
        result = []
        async for token in self.client.generate_completion_stream(trace):
            result.append(token)

        # Verify
        self.mock_get_messages.assert_called_once_with(trace, None)
        self.mock_async_client.chat.completions.create.assert_called_once_with(
            model=self.mock_config.llm.model,
            messages=[{"role": "user", "content": "test"}],
            temperature=self.mock_config.llm.temperature,
            top_p=self.mock_config.llm.top_p,
            presence_penalty=self.mock_config.llm.presence_penalty,
            stop=self.mock_config.llm.get_effective_stop_sequence(False),
            stream=True,
        )
        self.assertEqual(result, ["Test ", "stream"])

    async def test_generate_completion_stream_with_turns(self):
        """Test generate_completion_stream method with existing turns."""
        # Create a trace with turns
        output = ModelOutput(raw="Test output")
        turn = Turn(output=output, action_result="Test result")
        trace = Trace(query="Test query", turns=[turn])

        # Setup mock stream response
        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta.content = "Test stream"

        # Configure AsyncMock to return an async iterator
        self.mock_async_client.chat.completions.create.return_value.__aiter__.return_value = [
            chunk
        ]

        # Test
        result = []
        async for token in self.client.generate_completion_stream(trace):
            result.append(token)

        # Verify
        self.mock_async_client.chat.completions.create.assert_called_once_with(
            model=self.mock_config.llm.model,
            messages=[{"role": "user", "content": "test"}],
            temperature=self.mock_config.llm.temperature,
            top_p=self.mock_config.llm.top_p,
            presence_penalty=self.mock_config.llm.presence_penalty,
            stop=self.mock_config.llm.get_effective_stop_sequence(
                True
            ),  # Should be True with turns
            stream=True,
        )
        self.assertEqual(result, ["Test stream"])

    async def test_generate_completion_stream_error(self):
        """Test generate_completion_stream method with error."""
        # Setup
        self.mock_async_client.chat.completions.create.side_effect = Exception(
            "Test error"
        )

        # Test
        trace = Trace(query="Test query", turns=[])

        # Verify
        with self.assertRaises(Exception):
            async for _ in self.client.generate_completion_stream(trace):
                pass


if __name__ == "__main__":
    unittest.main()
