# tests/reasoning/models/test_trace.py

from ii_researcher.reasoning.models.trace import Turn, Trace
from ii_researcher.reasoning.models.output import ModelOutput
from ii_researcher.reasoning.models.action import Action
from ii_researcher.reasoning.config import ConfigConstants


class TestTurn:
    def test_init(self):
        """Test basic Turn initialization."""
        output = ModelOutput(raw="Test output")
        action_result = "Action result"
        suffix = "Test suffix"

        turn = Turn(output=output, action_result=action_result, suffix=suffix)

        assert turn.output == output
        assert turn.action_result == action_result
        assert turn.suffix == suffix

    def test_to_string_with_action(self):
        """Test to_string method with action."""
        action = Action(name="test_action", arguments={"arg": "value"})
        output = ModelOutput(action=action, raw="Test output with action")
        action_result = "Action result"
        suffix = "Test suffix"

        turn = Turn(output=output, action_result=action_result, suffix=suffix)

        result = turn.to_string()
        assert output.to_string() in result
        assert ConfigConstants.TOOL_RESPONSE_OPEN in result
        assert action_result in result
        assert ConfigConstants.TOOL_RESPONSE_CLOSE in result
        assert suffix in result

    def test_to_string_without_action(self):
        """Test to_string method without action."""
        output = ModelOutput(raw="Test output without action")
        action_result = "Action result"

        turn = Turn(output=output, action_result=action_result)

        assert turn.to_string() == output.raw

    def test_to_string_with_last_turn_flag(self):
        """Test to_string method with last_turn flag."""
        action = Action(name="test_action", arguments={"arg": "value"})
        output = ModelOutput(action=action, raw="Test output with action")
        action_result = "Action result"

        turn = Turn(output=output, action_result=action_result)

        # Compare results with and without last_turn flag
        result_normal = turn.to_string(last_turn=False)
        result_last = turn.to_string(last_turn=True)

        # Both should contain the same elements but might format differently
        assert output.to_string() in result_last
        assert ConfigConstants.TOOL_RESPONSE_OPEN in result_last
        assert action_result in result_last
        assert ConfigConstants.TOOL_RESPONSE_CLOSE in result_last


class TestTrace:
    def test_init(self):
        """Test basic Trace initialization."""
        query = "Test query"
        turns = []

        trace = Trace(query=query, turns=turns)

        assert trace.query == query
        assert trace.turns == turns

    def test_to_string_empty_turns(self):
        """Test to_string method with empty turns."""
        query = "Test query"
        trace = Trace(query=query, turns=[])

        result = trace.to_string()

        assert ConfigConstants.THINK_TAG_OPEN in result
        assert query in result
        assert "So, the user's question is:" in result

    def test_to_string_with_turns(self):
        """Test to_string method with turns."""
        query = "Test query"

        # Create some turns
        action = Action(name="test_action", arguments={"arg": "value"})
        output1 = ModelOutput(action=action, raw="Turn 1 output")
        turn1 = Turn(output=output1, action_result="Turn 1 result")

        output2 = ModelOutput(raw="Turn 2 output")
        turn2 = Turn(output=output2, action_result="Turn 2 result")

        trace = Trace(query=query, turns=[turn1, turn2])

        result = trace.to_string()

        assert ConfigConstants.THINK_TAG_OPEN in result
        assert query in result
        assert turn1.to_string() in result
        assert turn2.to_string() in result

    def test_to_string_with_instructions(self):
        """Test to_string method with instructions."""
        query = "Test query"
        instructions = "Test instructions"
        trace = Trace(query=query, turns=[])

        result = trace.to_string(instructions=instructions)

        assert ConfigConstants.THINK_TAG_OPEN in result
        assert query in result
        assert instructions in result

    def test_to_string_with_last_turn(self):
        """Test to_string method with is_last flag in the last turn."""
        query = "Test query"

        # Create a turn with is_last=True
        output = ModelOutput(raw="Last turn", is_last=True)
        turn = Turn(output=output, action_result="Result")

        trace = Trace(query=query, turns=[turn])

        result = trace.to_string()

        assert ConfigConstants.THINK_TAG_OPEN in result
        assert query in result
        assert turn.to_string() in result
        assert ConfigConstants.THINK_TAG_CLOSE in result
