# tests/reasoning/models/test_output.py
from ii_researcher.reasoning.models.output import ModelOutput, clean_streamed_output
from ii_researcher.reasoning.models.action import Action
from ii_researcher.reasoning.config import ConfigConstants


class TestModelOutput:
    def test_from_string_no_action(self):
        """Test parsing string with no action."""
        output_string = "This is a regular output with no action."
        output = ModelOutput.from_string(output_string)
        assert output.action is None
        assert output.raw == output_string
        assert output.is_last is False

    def test_from_string_with_action(self):
        """Test parsing string with an action."""
        action_string = 'search(query="test query")'
        output_string = f"Some reasoning\n```py\n{action_string}\n```\nMore text"
        output = ModelOutput.from_string(output_string, ["search"])

        assert output.action is not None
        assert output.action.name == "search"
        assert output.action.arguments == {"query": "test query"}
        assert output.raw == output_string
        assert output.is_last is False

    def test_from_string_invalid_action(self):
        """Test parsing string with an invalid action format."""
        output_string = "Some reasoning\n```py\ninvalid action syntax\n```\nMore text"
        output = ModelOutput.from_string(output_string, ["search"])

        assert output.action is None
        assert output.raw == output_string

    def test_short_format(self):
        """Test short format representation."""
        # With action
        action = Action(name="search", arguments={"query": "test query"})
        output = ModelOutput(action=action, raw="Original raw content")
        short_format = output.short_format()

        assert "Truncated reasoning" in short_format
        assert "Action:" in short_format
        assert "```py" in short_format
        assert 'search(query="test query")' in short_format
        assert f"{ConfigConstants.END_CODE}" in short_format

        # Without action
        output = ModelOutput(action=None, raw="Original raw content")
        assert output.short_format() == "Original raw content"

    def test_full_format(self):
        """Test full format representation."""
        output = ModelOutput(action=None, raw="  Raw content with spaces  ")
        assert (
            output.full_format() == "Raw content with spaces" + ConfigConstants.END_CODE
        )

        # Test with END_CODE already in the content
        output = ModelOutput(
            action=None, raw=f"Raw content with END_CODE{ConfigConstants.END_CODE}"
        )
        assert (
            output.full_format()
            == "Raw content with END_CODE" + ConfigConstants.END_CODE
        )

    def test_to_string(self):
        """Test to_string method."""
        # Normal case
        output = ModelOutput(action=None, raw="Regular output")
        assert output.to_string() == "Regular output" + ConfigConstants.END_CODE

        # With THINK_TAG_CLOSE in the raw content
        output = ModelOutput(
            action=None,
            raw=f"Some thinking{ConfigConstants.THINK_TAG_CLOSE}Final answer",
        )
        assert (
            output.to_string() == "Some thinkingFinal answer" + ConfigConstants.END_CODE
        )

    def test_is_last_flag(self):
        """Test is_last flag behavior."""
        output = ModelOutput(action=None, raw="Output", is_last=True)
        assert output.is_last is True

        output = ModelOutput(action=None, raw="Output")
        assert output.is_last is False


class TestCleanStreamedOutput:
    def test_clean_normal_text(self):
        """Test cleaning normal text without END_CODE."""
        text = "This is normal text"
        assert clean_streamed_output(text) == text

    def test_clean_text_with_end_code(self):
        """Test cleaning text with complete END_CODE."""
        text = f"Text with end code{ConfigConstants.END_CODE}"
        assert clean_streamed_output(text) == "Text with end code"

    def test_clean_text_with_partial_end_code(self):
        """Test cleaning text with partial END_CODE."""
        # Test with various partial END_CODE lengths
        for i in range(1, len(ConfigConstants.END_CODE)):
            partial_end_code = ConfigConstants.END_CODE[:i]
            text = f"Text with partial end code{partial_end_code}"
            assert clean_streamed_output(text) == "Text with partial end code"

    def test_clean_text_with_multiple_end_codes(self):
        """Test cleaning text with multiple END_CODE occurrences."""
        text = f"First part{ConfigConstants.END_CODE} Second part{ConfigConstants.END_CODE}"
        # Should only remove the last occurrence
        expected = f"First part{ConfigConstants.END_CODE} Second part"
        assert clean_streamed_output(text) == expected

    def test_clean_text_with_whitespace(self):
        """Test cleaning text with whitespace."""
        text = f"  Text with whitespace  {ConfigConstants.END_CODE}  "
        assert clean_streamed_output(text) == "Text with whitespace  "
