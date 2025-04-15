import asyncio
import logging
import re
from argparse import ArgumentParser
from dotenv import load_dotenv

load_dotenv()

from ii_researcher_legacy.ii_researcher.pipeline.agent import DeepSearchAgent


async def main(
    question: str,
    save_report: bool = False,
    is_stream: bool = False,
):
    """Main entry point for the agent that combines normal deep search and reasoning capabilities."""

    def on_token(token: str):
        """Callback for processing streamed tokens."""
        print(token, end="", flush=True)

    # Initialize and run the appropriate agent based on the mode
    agent = DeepSearchAgent()
    result = await agent.search(question, max_steps=30)

    if save_report:
        result_file = re.sub(r"[^a-zA-Z0-9]", "_", question)[:100] + ".md"
        with open(result_file, "w") as f:
            f.write(result)
        logging.info(f"Saved result to {result_file}")

    return result


if __name__ == "__main__":
    parser = ArgumentParser(description="AI Research Agent")
    parser.add_argument("--question", type=str, required=True, help="The question to research")
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save the result to a markdown file",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream the result",
    )
    args = parser.parse_args()

    asyncio.run(
        main(
            question=args.question,
            save_report=args.save_report,
            is_stream=args.stream,
        ))
