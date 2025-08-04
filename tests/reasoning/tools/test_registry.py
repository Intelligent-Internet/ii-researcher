import unittest
from ii_researcher.reasoning.tools.registry import (
    ToolRegistry,
    registry,
    register_tool,
    get_tool,
    list_tools,
    get_all_tools,
    format_tool_descriptions,
)
from ii_researcher.reasoning.tools.base import BaseTool


class MockTool(BaseTool):
    """Mock tool for testing."""

    name = "mock_tool"
    description = "Mock tool for testing"
    argument_schema = {"arg1": {"type": "string"}}
    return_type = "string"
    suffix = ""

    async def execute(self, tool_history=None, **kwargs):
        return "mock result"

    @classmethod
    def reset(cls):
        pass


class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        """Reset registry before each test."""
        # Keep a reference to the real tools
        self.original_tools = registry._tools.copy()
        # Clear the registry
        registry._tools = {}

    def tearDown(self):
        """Restore original tools after each test."""
        registry._tools = self.original_tools

    def test_singleton_pattern(self):
        """Test that ToolRegistry follows the singleton pattern."""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()
        self.assertIs(registry1, registry2)

    def test_register_tool(self):
        """Test registering a tool."""
        registry.register(MockTool)
        self.assertIn("mock_tool", registry._tools)
        self.assertEqual(registry._tools["mock_tool"], MockTool)

    def test_register_tool_decorator(self):
        """Test the register_tool decorator."""

        @register_tool
        class TestTool(BaseTool):
            name = "test_tool"
            description = "Test tool"
            argument_schema = {}
            return_type = "string"
            suffix = ""

            async def execute(self, tool_history=None, **kwargs):
                return "test result"

            @classmethod
            def reset(cls):
                pass

        self.assertIn("test_tool", registry._tools)
        self.assertEqual(registry._tools["test_tool"], TestTool)

    def test_register_tool_without_name(self):
        """Test registering a tool without a name raises ValueError."""

        class NoNameTool(BaseTool):
            description = "Tool without name"
            argument_schema = {}
            return_type = "string"
            suffix = ""

            async def execute(self, tool_history=None, **kwargs):
                return "result"

            @classmethod
            def reset(cls):
                pass

        with self.assertRaises(ValueError):
            registry.register(NoNameTool)

    def test_get_tool(self):
        """Test getting a tool by name."""
        registry.register(MockTool)
        self.assertEqual(registry.get_tool("mock_tool"), MockTool)
        self.assertIsNone(registry.get_tool("nonexistent_tool"))

        # Test the module function
        self.assertEqual(get_tool("mock_tool"), MockTool)

    def test_list_tools(self):
        """Test listing all registered tools."""
        registry.register(MockTool)

        @register_tool
        class AnotherTool(BaseTool):
            name = "another_tool"
            description = "Another test tool"
            argument_schema = {}
            return_type = "string"
            suffix = ""

            async def execute(self, tool_history=None, **kwargs):
                return "result"

            @classmethod
            def reset(cls):
                pass

        tool_list = registry.list_tools()
        self.assertIn("mock_tool", tool_list)
        self.assertIn("another_tool", tool_list)
        self.assertEqual(len(tool_list), 2)

        # Test the module function
        self.assertEqual(list_tools(), tool_list)

    def test_get_all_tools(self):
        """Test getting all registered tools."""
        registry.register(MockTool)
        tools_dict = registry.get_all_tools()
        self.assertIn("mock_tool", tools_dict)
        self.assertEqual(tools_dict["mock_tool"], MockTool)

        # Test the module function
        self.assertEqual(get_all_tools(), tools_dict)

    def test_format_tool_descriptions(self):
        """Test formatting tool descriptions."""
        registry.register(MockTool)

        expected_description = (
            "*You only have access to these tools:\n"
            + "- mock_tool: Mock tool for testing\n"
            + "    Takes inputs: {'arg1': {'type': 'string'}}\n"
            + "    Returns an output of type: string"
        )

        self.assertEqual(registry.format_tool_descriptions(), expected_description)

        # Test the module function
        self.assertEqual(format_tool_descriptions(), expected_description)

    def test_tool_sorting_in_descriptions(self):
        """Test that web_search and page_visit tools come first in descriptions."""

        # Register tools in wrong order to test sorting
        @register_tool
        class ZTool(BaseTool):
            name = "z_tool"
            description = "Z tool"
            argument_schema = {}
            return_type = "string"
            suffix = ""

            async def execute(self, tool_history=None, **kwargs):
                return "z result"

            @classmethod
            def reset(cls):
                pass

        @register_tool
        class PageVisitTool(BaseTool):
            name = "page_visit"
            description = "Page visit tool"
            argument_schema = {}
            return_type = "string"
            suffix = ""

            async def execute(self, tool_history=None, **kwargs):
                return "page visit result"

            @classmethod
            def reset(cls):
                pass

        @register_tool
        class WebSearchTool(BaseTool):
            name = "web_search"
            description = "Web search tool"
            argument_schema = {}
            return_type = "string"
            suffix = ""

            async def execute(self, tool_history=None, **kwargs):
                return "web search result"

            @classmethod
            def reset(cls):
                pass

        @register_tool
        class ATool(BaseTool):
            name = "a_tool"
            description = "A tool"
            argument_schema = {}
            return_type = "string"
            suffix = ""

            async def execute(self, tool_history=None, **kwargs):
                return "a result"

            @classmethod
            def reset(cls):
                pass

        description = registry.format_tool_descriptions()
        # Check that web_search comes first
        self.assertTrue(
            description.index("web_search") < description.index("page_visit")
        )
        # Check that page_visit comes before other tools
        self.assertTrue(description.index("page_visit") < description.index("a_tool"))
        self.assertTrue(description.index("page_visit") < description.index("z_tool"))
