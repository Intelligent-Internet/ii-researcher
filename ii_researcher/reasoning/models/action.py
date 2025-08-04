import ast
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from ii_researcher.reasoning.utils import evaluate_ast_node


class Action(BaseModel):
    """A model representing an action with a name and arguments."""

    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_string(cls, string: str) -> Optional["Action"]:
        """
        Parse a string into an Action instance.

        Args:
            string: A string in format "action_name(arg1=value1, arg2=value2)"

        Returns:
            Action instance if parsing succeeds, None otherwise

        Raises:
            ValueError: If the string format is invalid
        """
        try:
            # Remove leading/trailing whitespace
            string = string.strip()

            # Check if string contains function call pattern
            if not (string.endswith(")") and "(" in string):
                raise ValueError(
                    f"String must be in format 'name(arg1=value1, arg2=...)' but got {string}"
                )

            # Parse the AST
            tree = ast.parse(string)
            if not tree.body or not isinstance(tree.body[0].value, ast.Call):
                raise ValueError("String must contain a valid function call")

            call = tree.body[0].value
            name = getattr(call.func, "id", None)
            if not name:
                raise ValueError("Action name must be a valid identifier")

            # Process keyword arguments
            arguments = {}
            for keyword in call.keywords:
                if not keyword.arg:
                    raise ValueError("All arguments must be named (keyword arguments)")

                # Extract the value using ast.literal_eval for complex structures
                value = evaluate_ast_node(keyword.value)
                arguments[keyword.arg] = value

            return cls(name=name, arguments=arguments)

        except SyntaxError as e:
            raise ValueError(f"Invalid action string syntax: {str(e)}") from e
        except ValueError as e:
            raise ValueError(f"Invalid action string format: {str(e)}") from e
        except Exception as e:
            raise ValueError(f"Unexpected error parsing action string: {str(e)}") from e

    def to_string(self) -> str:
        """
        Convert Action instance to a string in function call format.

        Returns:
            String in format "name(arg1=value1, arg2=value2)"
        """
        args = []
        for key, value in self.arguments.items():
            # Handle string values with proper quoting
            if isinstance(value, str):
                arg_str = f'{key}="{value}"'
            # Handle other types (numbers, booleans, etc.) without quotes
            else:
                arg_str = f"{key}={value}"
            args.append(arg_str)

        args_str = ", ".join(args)
        return f"{self.name}({args_str})"
