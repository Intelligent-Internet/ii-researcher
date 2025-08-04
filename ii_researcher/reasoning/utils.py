import ast
import re
from typing import Any, List


def parse_code_blobs(text: str, tool_names: List[str] = None) -> str:
    """Extract code blocks from the LLM's output.

    If a valid code block is passed, it returns it directly.

    Args:
        text (`str`): LLM's output text to parse.
        tool_names (`List[str]`, optional): List of tool names to check in the code block.

    Returns:
        `str`: Extracted code block.
    """
    # Try to extract code from markdown blocks first
    if tool_names:
        tool_names_pattern = "|".join(map(re.escape, tool_names))
        pattern = rf"```\s*(?:py|python)\s*(.*?(?:{tool_names_pattern}).*?)\s*```"
    else:
        pattern = r"```\s*(?:py|python)\s*(.*?)\s*```"

    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[-1].strip()

    # Maybe the LLM outputted a code blob directly
    try:
        ast.parse(text)
        return text
    except SyntaxError:
        pass

    return ""


def evaluate_ast_node(node: ast.AST) -> Any:
    """
    Recursively evaluate an AST node to extract its value.

    Args:
        node: An AST node representing a value

    Returns:
        The Python value represented by the node

    Raises:
        ValueError: If the node cannot be evaluated
    """
    # Handle simple literals directly
    if isinstance(node, ast.Constant):
        return node.value

    # Handle lists
    if isinstance(node, ast.List):
        return [evaluate_ast_node(elem) for elem in node.elts]

    # Handle dictionaries
    if isinstance(node, ast.Dict):
        keys = [evaluate_ast_node(k) for k in node.keys]
        values = [evaluate_ast_node(v) for v in node.values]
        return dict(zip(keys, values))

    # Handle tuples
    if isinstance(node, ast.Tuple):
        return tuple(evaluate_ast_node(elem) for elem in node.elts)

    # Handle sets
    if isinstance(node, ast.Set):
        return {evaluate_ast_node(elem) for elem in node.elts}

    if isinstance(node, ast.Name):
        # Handle special constants like True, False, None
        if node.id == "True":
            return True
        if node.id == "False":
            return False
        if node.id == "None":
            return None
        raise ValueError(f"Cannot evaluate name: {node.id}")

    # For more complex expressions, try using ast.literal_eval
    try:
        # Convert the node to source code
        code = ast.unparse(node)
        # Use ast.literal_eval to safely evaluate expressions
        return ast.literal_eval(code)
    except (AttributeError, ValueError) as exc:
        # For Python versions without ast.unparse or other issues
        raise ValueError(
            f"Cannot evaluate complex expression: {ast.dump(node)}"
        ) from exc
