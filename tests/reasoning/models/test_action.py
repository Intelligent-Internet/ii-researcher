# tests/reasoning/test_action.py
import pytest
from ii_researcher.reasoning.models.action import Action


class TestAction:
    def test_init(self):
        """Test basic Action initialization."""
        action = Action(name="test_action", arguments={"arg1": "value1", "arg2": 42})
        assert action.name == "test_action"
        assert action.arguments == {"arg1": "value1", "arg2": 42}

    def test_from_string_basic(self):
        """Test parsing a simple action string."""
        string = 'search(query="test query")'
        action = Action.from_string(string)
        assert action.name == "search"
        assert action.arguments == {"query": "test query"}

    def test_from_string_multiple_args(self):
        """Test parsing action string with multiple arguments."""
        string = 'analyze(text="sample text", max_tokens=100, include_metadata=True)'
        action = Action.from_string(string)
        assert action.name == "analyze"
        assert action.arguments == {
            "text": "sample text",
            "max_tokens": 100,
            "include_metadata": True,
        }

    def test_from_string_no_args(self):
        """Test parsing action string with no arguments."""
        string = "list_all()"
        action = Action.from_string(string)
        assert action.name == "list_all"
        assert action.arguments == {}

    def test_from_string_complex_values(self):
        """Test parsing action string with complex argument values."""
        string = 'complex_action(numbers=[1, 2, 3], mapping={"a": 1, "b": 2}, flag=True, value=None)'
        action = Action.from_string(string)
        assert action.name == "complex_action"
        assert action.arguments == {
            "numbers": [1, 2, 3],
            "mapping": {"a": 1, "b": 2},
            "flag": True,
            "value": None,
        }

    def test_from_string_nested_structures(self):
        """Test parsing action string with nested data structures."""
        string = 'nested_action(data={"items": [1, 2, {"nested": True}], "tuple": (1, 2, 3)})'
        action = Action.from_string(string)
        assert action.name == "nested_action"
        assert action.arguments["data"]["items"] == [1, 2, {"nested": True}]
        assert action.arguments["data"]["tuple"] == (1, 2, 3)

    def test_to_string_basic(self):
        """Test converting Action to string."""
        action = Action(name="search", arguments={"query": "test query"})
        result = action.to_string()
        assert result == 'search(query="test query")'

    def test_to_string_multiple_args(self):
        """Test converting Action with multiple arguments to string."""
        action = Action(
            name="analyze",
            arguments={
                "text": "sample text",
                "max_tokens": 100,
                "include_metadata": True,
            },
        )
        result = action.to_string()
        # Since dict order isn't guaranteed, we check parts of the string
        assert "analyze(" in result
        assert 'text="sample text"' in result
        assert "max_tokens=100" in result
        assert "include_metadata=True" in result

    def test_to_string_no_args(self):
        """Test converting Action with no arguments to string."""
        action = Action(name="list_all", arguments={})
        result = action.to_string()
        assert result == "list_all()"

    def test_from_string_invalid_formats(self):
        """Test error handling for invalid string formats."""
        invalid_strings = [
            "not_a_function",
            "missing_parens",
            "incorrect(syntax",
            "wrong_syntax)",
            "invalid argument=value)",
            "no_name(arg=value)",
        ]

        for string in invalid_strings:
            with pytest.raises(ValueError):
                Action.from_string(string)

    def test_from_string_invalid_variable(self):
        """Test error when string contains a variable reference."""
        with pytest.raises(ValueError):
            Action.from_string("action(arg=variable_name)")

    def test_roundtrip_conversion(self):
        """Test round-trip conversion: string -> Action -> string."""
        original = 'test_action(arg1="value", arg2=42, flag=True)'
        action = Action.from_string(original)
        result = action.to_string()

        # Extract the parts since argument order might differ
        assert "test_action(" in result
        assert 'arg1="value"' in result
        assert "arg2=42" in result
        assert "flag=True" in result

        # Verify we can parse it back again
        action2 = Action.from_string(result)
        assert action2.name == action.name
        assert action2.arguments == action.arguments
