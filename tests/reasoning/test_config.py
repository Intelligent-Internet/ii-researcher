import os
from unittest.mock import patch

from ii_researcher.reasoning.config import (
    ConfigConstants,
    ToolConfig,
    LLMConfig,
    AgentConfig,
    ReportConfig,
    get_config,
    get_report_config,
    update_config,
)


class TestConfigConstants:
    def test_constants_exist(self):
        # Verify all constants are defined
        assert hasattr(ConfigConstants, "THINK_TAG_OPEN")
        assert hasattr(ConfigConstants, "THINK_TAG_CLOSE")
        assert hasattr(ConfigConstants, "TOOL_RESPONSE_OPEN")
        assert hasattr(ConfigConstants, "TOOL_RESPONSE_CLOSE")
        assert hasattr(ConfigConstants, "CODE_BLOCK_START")
        assert hasattr(ConfigConstants, "CODE_BLOCK_END")
        assert hasattr(ConfigConstants, "END_CODE")
        assert hasattr(ConfigConstants, "INSTRUCTIONS_OPEN")
        assert hasattr(ConfigConstants, "INSTRUCTIONS_CLOSE")

    def test_constant_values(self):
        # Test specific values
        assert ConfigConstants.THINK_TAG_OPEN == "<think>"
        assert ConfigConstants.THINK_TAG_CLOSE == "</think>"
        assert ConfigConstants.CODE_BLOCK_START == "```py"
        assert ConfigConstants.CODE_BLOCK_END == "```"

    def test_tool_call_example_format(self):
        # Verify the tool call example has the expected format
        assert ConfigConstants.CODE_BLOCK_START in ConfigConstants.TOOL_CALL_EXAMPLE
        assert ConfigConstants.CODE_BLOCK_END in ConfigConstants.TOOL_CALL_EXAMPLE
        assert ConfigConstants.END_CODE in ConfigConstants.TOOL_CALL_EXAMPLE
        assert "web_search" in ConfigConstants.TOOL_CALL_EXAMPLE
        assert "page_visit" in ConfigConstants.TOOL_CALL_EXAMPLE


class TestToolConfig:
    def test_default_values(self):
        config = ToolConfig()
        assert config.max_search_results == 4
        assert config.max_search_queries == 2
        assert config.max_urls_to_visit == 3
        # This will use the value from SEARCH_PROVIDER environment variable
        assert isinstance(config.search_provider, str)


class TestLLMConfig:
    @patch.dict(
        os.environ,
        {"R_MODEL": "test-model", "R_TEMPERATURE": "0.5", "OPENAI_API_KEY": "test-key"},
    )
    def test_env_variable_config(self):
        config = LLMConfig()
        assert config.model == "test-model"
        assert config.temperature == 0.5
        assert config.api_key == "test-key"

    def test_default_values(self):
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig()
            assert config.model == "r1"  # Default when R_MODEL not set
            assert config.temperature == 0.2  # Default when R_TEMPERATURE not set
            assert config.top_p == 0.95
            assert config.presence_penalty == 0
            assert config.stop_sequence == ConfigConstants.DEFAULT_STOP_SEQUENCE

    def test_get_effective_stop_sequence(self):
        config = LLMConfig()
        # Without turns
        assert (
            config.get_effective_stop_sequence(trace_has_turns=False)
            == ConfigConstants.DEFAULT_STOP_SEQUENCE
        )

        # With turns - should include THINK_TAG_CLOSE
        with_turns_stop = config.get_effective_stop_sequence(trace_has_turns=True)
        assert ConfigConstants.THINK_TAG_CLOSE in with_turns_stop

        # Make sure we have a set (no duplicates)
        assert len(with_turns_stop) == len(set(with_turns_stop))


class TestAgentConfig:
    def test_config_initialization(self):
        config = AgentConfig()
        assert isinstance(config.tool, ToolConfig)
        assert isinstance(config.llm, LLMConfig)
        assert "II Researcher" in config.system_prompt
        assert ConfigConstants.INSTRUCTIONS_OPEN in config.instructions

    def test_templates(self):
        config = AgentConfig()
        assert (
            config.duplicate_query_template == ConfigConstants.DUPLICATE_QUERY_TEMPLATE
        )
        assert config.duplicate_url_template == ConfigConstants.DUPLICATE_URL_TEMPLATE


class TestReportConfig:
    def test_config_initialization(self):
        config = ReportConfig()
        assert isinstance(config.llm, LLMConfig)

    def test_generate_introduction_messages(self):
        config = ReportConfig()
        trace = "Sample trace data"
        query = "Sample query"
        messages = config.generate_introduction_messages(trace, query)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert query in messages[1]["content"]
        assert trace in messages[1]["content"]
        assert "introduction" in messages[1]["content"].lower()

    def test_generate_subtopics_messages(self):
        config = ReportConfig()
        trace = "Sample trace data"
        query = "Sample query"
        messages = config.generate_subtopics_messages(trace, query)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert query in messages[1]["content"]
        assert trace in messages[1]["content"]
        assert "subtopics" in messages[1]["content"].lower()

    def test_generate_subtopic_report_messages(self):
        config = ReportConfig()
        trace = "Sample trace data"
        content_from_previous = "Previous content"
        subtopics = ["Topic 1", "Topic 2"]
        current_subtopic = "Topic 1"
        query = "Sample query"

        messages = config.generate_subtopic_report_messages(
            trace, content_from_previous, subtopics, current_subtopic, query
        )

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert query in messages[1]["content"]
        assert trace in messages[1]["content"]
        assert current_subtopic in messages[1]["content"]
        assert content_from_previous in messages[1]["content"]

    def test_generate_report_messages(self):
        config = ReportConfig()
        trace = "Sample trace data"
        query = "Sample query"
        messages = config.generate_report_messages(trace, query)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert query in messages[1]["content"]
        assert trace in messages[1]["content"]
        assert "report" in messages[1]["content"].lower()


class TestConfigFunctions:
    def test_get_config(self):
        # Verify we get the singleton instance
        config = get_config()
        assert isinstance(config, AgentConfig)

    def test_get_report_config(self):
        # Verify we get the singleton instance
        report_config = get_report_config()
        assert isinstance(report_config, ReportConfig)

    def test_update_config(self):
        # Save original config
        original_config = get_config()
        original_prompt = original_config.system_prompt

        # Update a field
        test_prompt = "Test prompt"
        update_config({"system_prompt": test_prompt})

        # Verify the update worked
        updated_config = get_config()
        assert updated_config.system_prompt == test_prompt

        # Restore original value
        update_config({"system_prompt": original_prompt})
