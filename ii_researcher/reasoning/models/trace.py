from typing import List, Optional

from pydantic import BaseModel

from ii_researcher.reasoning.config import ConfigConstants
from ii_researcher.reasoning.models.output import ModelOutput


class Turn(BaseModel):
    """A model representing a single turn in the conversation."""

    output: ModelOutput
    action_result: str
    suffix: Optional[str] = None

    def to_string(self, last_turn: bool = False) -> str:
        """Convert the turn to a string."""
        if self.output.action:
            if last_turn:
                return f"{self.output.to_string()}\n\n{ConfigConstants.TOOL_RESPONSE_OPEN}{self.action_result}{ConfigConstants.TOOL_RESPONSE_CLOSE}\n{self.suffix if self.suffix else ''}"
            return f"{self.output.to_string()}\n\n{ConfigConstants.TOOL_RESPONSE_OPEN}{self.action_result}{ConfigConstants.TOOL_RESPONSE_CLOSE}\n{self.suffix if self.suffix else ''}"

        return self.output.raw


class Trace(BaseModel):
    """A model representing the entire conversation trace."""

    query: str
    turns: List[Turn]

    def to_string(self, instructions: Optional[str] = None) -> str:
        """Convert the trace to a string."""
        return_string = ""
        turn_messages = []
        for i, turn in enumerate(self.turns):
            is_last_turn = i == len(self.turns) - 1
            turn_messages.append(turn.to_string(last_turn=is_last_turn))

        if len(self.turns) == 0:
            return_string = (
                f"{ConfigConstants.THINK_TAG_OPEN} {instructions if instructions else ''} \nSo, the user's question is: '{self.query}' \n"
                + "\n".join(turn_messages)
            )
        else:
            return_string = (
                f"{ConfigConstants.THINK_TAG_OPEN} So, the user's question is: '{self.query}' "
                + "\n".join(turn_messages)
                + f"\n{instructions if instructions else ''}"
            )

        if (
            len(self.turns) > 0
            and self.turns[-1].output.is_last
            and (not return_string.strip().endswith(ConfigConstants.THINK_TAG_CLOSE))
        ):
            return_string += ConfigConstants.THINK_TAG_CLOSE

        return return_string
