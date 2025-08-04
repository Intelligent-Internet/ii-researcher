from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from ii_researcher.reasoning.agent import ReasoningAgent

# Load environment variables
load_dotenv()

# Create an MCP server
mcp = FastMCP("II-Researcher")


@mcp.tool()
async def search(question: str) -> str:
    """
    Performs comprehensive web research on the provided question using II-Researcher.
    This tool is ideal for retrieving up-to-date information such as current events,
    market data, biographical details, or specialized knowledge that requires
    real-time sources.

    Args:
        question: The research query or topic

    Returns:
        A string containing the research results
    """
    agent = ReasoningAgent(question=question)
    result = await agent.run()
    return result


if __name__ == "__main__":
    mcp.run()
