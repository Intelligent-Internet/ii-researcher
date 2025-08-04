import ast
import pytest
from ii_researcher.reasoning.utils import parse_code_blobs, evaluate_ast_node


class TestParseCodeBlobs:
    def test_extract_from_markdown_block(self):
        text = """
        Here's some code:
        ```py
        def hello():
            print("Hello World")
        ```
        """
        result = parse_code_blobs(text)
        assert result == 'def hello():\n            print("Hello World")'

    def test_extract_with_tool_names(self):
        text = """
        Here's some code:
        ```py
        def use_search_tool():
            result = search("query")
            return result
        ```
        """
        result = parse_code_blobs(text, tool_names=["search"])
        assert (
            result
            == 'def use_search_tool():\n            result = search("query")\n            return result'
        )

    def test_direct_code_input(self):
        text = 'def hello():\n    print("Hello World")'
        result = parse_code_blobs(text)
        assert result == 'def hello():\n    print("Hello World")'

    def test_no_code_found(self):
        text = "This is just text with no code"
        result = parse_code_blobs(text)
        assert result == ""


class TestEvaluateAstNode:
    def test_constant_value(self):
        node = ast.Constant(value=42)
        result = evaluate_ast_node(node)
        assert result == 42

    def test_list_value(self):
        # Create a list node [1, 2, 3]
        node = ast.List(
            elts=[ast.Constant(value=1), ast.Constant(value=2), ast.Constant(value=3)]
        )
        result = evaluate_ast_node(node)
        assert result == [1, 2, 3]

    def test_dict_value(self):
        # Create a dict node {"a": 1, "b": 2}
        node = ast.Dict(
            keys=[ast.Constant(value="a"), ast.Constant(value="b")],
            values=[ast.Constant(value=1), ast.Constant(value=2)],
        )
        result = evaluate_ast_node(node)
        assert result == {"a": 1, "b": 2}

    def test_tuple_value(self):
        # Create a tuple node (1, 2, 3)
        node = ast.Tuple(
            elts=[ast.Constant(value=1), ast.Constant(value=2), ast.Constant(value=3)]
        )
        result = evaluate_ast_node(node)
        assert result == (1, 2, 3)

    def test_set_value(self):
        # Create a set node {1, 2, 3}
        node = ast.Set(
            elts=[ast.Constant(value=1), ast.Constant(value=2), ast.Constant(value=3)]
        )
        result = evaluate_ast_node(node)
        assert result == {1, 2, 3}

    def test_special_constants(self):
        # Test True, False and None values
        true_node = ast.Name(id="True")
        false_node = ast.Name(id="False")
        none_node = ast.Name(id="None")

        assert evaluate_ast_node(true_node) is True
        assert evaluate_ast_node(false_node) is False
        assert evaluate_ast_node(none_node) is None

    def test_unsupported_name(self):
        # Test a variable name that can't be evaluated statically
        node = ast.Name(id="some_var")
        with pytest.raises(ValueError):
            evaluate_ast_node(node)
