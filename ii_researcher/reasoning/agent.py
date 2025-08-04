import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

from ii_researcher.reasoning.builders.report import ReportBuilder
from ii_researcher.reasoning.tools.tool_history import ToolHistory
from ii_researcher.reasoning.clients.openai_client import OpenAIClient
from ii_researcher.reasoning.config import get_config, update_config
from ii_researcher.reasoning.models.action import Action
from ii_researcher.reasoning.models.output import ModelOutput
from ii_researcher.reasoning.models.trace import Trace, Turn
from ii_researcher.reasoning.tools.registry import (
    format_tool_descriptions,
    get_all_tools,
    get_tool,
)
from ii_researcher.reasoning.builders.report import ReportType


class ReasoningAgent:
    """AI agent that performs research and answers questions."""

    def __init__(
        self,
        question: str,
        report_type: ReportType = ReportType.ADVANCED,
        stream_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        override_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the agent.

        Args:
            question: The research question to answer
            stream_event: Optional callback for streaming events
        """
        self.question = question
        self.tool_history = ToolHistory()
        self.trace = Trace(query=question, turns=[])
        self.client = OpenAIClient()
        self.config = get_config()
        if override_config:
            update_config(override_config)
        self.stream_event = stream_event
        self.report_type = report_type

        # Update system prompt with available tools and current date
        available_tools = format_tool_descriptions()
        self.instructions = self.config.instructions.format(
            current_date=datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
            available_tools=available_tools,
        )

        for tool in get_all_tools().values():
            tool.reset()

        logging.info("ReasoningAgent initialized with question: %s", question)

    async def process_stream(
        self, stream_generator, callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """Process a stream of tokens with timeout handling."""
        content = ""
        try:
            async for token in stream_generator:
                content += token
                if callback:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(token)
                    else:
                        callback(token)

                # Check if we've reached a stop token or end of stream
                for stop_token in self.config.llm.stop_sequence:
                    if stop_token in content:
                        return content
        except (asyncio.TimeoutError, asyncio.CancelledError) as e:
            logging.error("Error processing stream: %s", str(e))

        return content

    async def execute_action(self, action: Action) -> Tuple[str, Optional[str]]:
        """Execute an action, Return action result and suffix."""
        logging.info("Executing action: %s", action.name)

        tool_cls = get_tool(action.name)
        if not tool_cls:
            return f"Error: Tool '{action.name}' not found.", None

        tool = tool_cls()
        try:
            # Add the question as context for tools that need it
            action.arguments["question"] = self.question
            result = ""
            if self.stream_event:
                result = await tool.execute_stream(
                    self.stream_event, self.tool_history, **action.arguments
                )
            else:
                result = await tool.execute(self.tool_history, **action.arguments)

            return result, tool.suffix
        except (ValueError, KeyError, RuntimeError) as e:
            logging.error("Error executing action %s: %s", action.name, str(e))
            return f"Error executing {action.name}: {str(e)}", None

    async def run(
        self, on_token: Optional[Callable[[str], None]] = None, is_stream: bool = False
    ) -> str:
        """Run the agent."""
        turn = 0

        while True:
            # Generate streamed completion
            content = ""
            try:
                if is_stream:
                    stream_generator = self.client.generate_completion_stream(
                        self.trace, self.instructions
                    )
                    content = await self.process_stream(stream_generator, on_token)
                else:
                    content = self.client.generate_completion(
                        self.trace, self.instructions
                    )
            except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                logging.error("Error generating completion: %s", str(e))
                content = f"Error: {str(e)}"

            turn += 1

            # Parse the output
            try:
                model_output = ModelOutput.from_string(
                    content, tool_names=get_all_tools().keys()
                )
            except (ValueError, KeyError) as e:
                logging.error("Error parsing model output: %s", str(e))
                model_output = ModelOutput(raw=content)

            # Handle normal action/response case
            if model_output.action:
                logging.info("Processing action: %s", model_output.action.name)

                # Execute the action
                action_result, suffix = await self.execute_action(model_output.action)

                # Add the turn to the trace
                self.trace.turns.append(
                    Turn(
                        output=model_output, action_result=action_result, suffix=suffix
                    )
                )

            else:
                # Mark this as the last output
                model_output.is_last = True
                self.trace.turns.append(
                    Turn(output=model_output, action_result="", suffix=None)
                )

                # Generate the report
                try:
                    report_builder = ReportBuilder(self.stream_event)
                    if is_stream:
                        # Stream the report
                        final_report = await report_builder.generate_stream(
                            self.tool_history, self.trace, self.report_type, on_token
                        )
                    else:
                        final_report = report_builder.generate(
                            self.tool_history, self.trace, self.report_type
                        )

                    # Create a final turn with the report
                    report_output = ModelOutput(raw=final_report, is_last=True)
                    self.trace.turns.append(
                        Turn(output=report_output, action_result="", suffix=None)
                    )

                    return final_report

                except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                    logging.error("Error generating report: %s", str(e))
                    return f"Error generating report: {str(e)}"

            await asyncio.sleep(1)
