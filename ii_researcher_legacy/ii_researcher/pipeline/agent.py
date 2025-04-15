"""
Core agent implementation for II Deep Search
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from baml_client.async_client import b
from baml_client.types import Answer, KnowledgeType, Reflect, Search, Visit
from ii_researcher_legacy.ii_researcher.config import (
    SCRAPE_URL_TIMEOUT,
    SEARCH_PROCESS_TIMEOUT,
    SEARCH_PROVIDER,
    SEARCH_QUERY_TIMEOUT,
    STEP_SLEEP,
)
from ii_researcher_legacy.ii_researcher.events import Event
from ii_researcher_legacy.ii_researcher.pipeline.action_handler.answer import AnswerHandler
from ii_researcher_legacy.ii_researcher.pipeline.action_handler.reflect import ReflectHandler
from ii_researcher_legacy.ii_researcher.pipeline.action_handler.search import SearchHandler
from ii_researcher_legacy.ii_researcher.pipeline.action_handler.visit import VisitHandler
from ii_researcher_legacy.ii_researcher.pipeline.evaluator import evaluate_question
from ii_researcher_legacy.ii_researcher.pipeline.schemas import ActionWithThinkB
from ii_researcher_legacy.ii_researcher.pipeline.state import ActionState, AgentState
from ii_researcher_legacy.ii_researcher.utils.url_tools import get_unvisited_urls


@dataclass
class AgentConfig:
    """Configuration for the DeepSearchAgent"""

    max_queries_per_step: int = 3
    max_urls_per_step: int = 2
    max_reflect_per_step: int = 3
    step_sleep_ms: int = STEP_SLEEP
    max_bad_attempts: int = 3
    max_website_per_query: int = 3
    search_provider: str = SEARCH_PROVIDER
    search_process_timeout: int = SEARCH_PROCESS_TIMEOUT
    search_query_timeout: int = SEARCH_QUERY_TIMEOUT
    scrape_url_timeout: int = SCRAPE_URL_TIMEOUT


class DeepSearchAgent:
    """Agent for deep search"""

    def __init__(
            self,
            config: AgentConfig = AgentConfig(),
            stream_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        """
        Initialize the agent

        Args:
            config: Configuration for the agent
            stream_event: Function to stream events
        """
        self.config = config
        self.stream_event = stream_event

        # Initialize state
        self.state = AgentState()

        # Set up action state with config and stream event
        self.action_state = ActionState(agent_state=self.state, config=self.config, stream_event=self.stream_event)

        # Initialize action handlers
        self.handlers = {
            Search: SearchHandler(self.action_state),
            Visit: VisitHandler(self.action_state),
            Reflect: ReflectHandler(self.action_state),
            Answer: AnswerHandler(self.action_state),
        }

    def _reset_state(self) -> None:
        """Reset the agent's state"""
        self.state.reset()

    async def sleep(self) -> None:
        """Sleep for the specified number of milliseconds."""
        seconds = self.config.step_sleep_ms / 1000
        print(f"Waiting {seconds:.1f}s...")
        await asyncio.sleep(seconds)

    def _get_current_date(self) -> str:
        """Get the current date in YYYY-MM-DD HH:MM:SS format"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def generate_action(self, question: str) -> ActionWithThinkB:
        """Generate the next action based on the current state"""
        current_date = self._get_current_date()

        # Get unvisited URLs and convert them to display format
        unvisited_urls = get_unvisited_urls(self.state.all_urls, self.state.visited_urls)
        display_unvisited_urls = []
        for url_data in unvisited_urls:
            url_copy = url_data.copy()
            if "url" in url_copy:
                url_copy["original_url"] = url_copy["url"]
                url_copy["url"] = self.state.get_url_id(url_copy["url"])
            display_unvisited_urls.append(url_copy)

        action_with_think = await b.GenerateAction(
            knowledges=self.state.knowledge_source.get_knowledge_by_types([
                KnowledgeType.QA,
                KnowledgeType.URL,
                KnowledgeType.Strategy,
                KnowledgeType.SearchInfo,
            ]),
            question=question,
            current_date=current_date,
            allow_reflect=self.state.allow_reflect,
            allow_read=self.state.allow_read,
            allow_answer=self.state.allow_answer,
            allow_search=self.state.allow_search,
            all_keywords=self.state.all_keywords,
            url_list=display_unvisited_urls,
            bad_context=self.state.bad_context,
            context=self.state.diary_context,
        )
        # Convert ActionWithThink to a dictionary first, then create ActionWithThinkB
        action_dict = action_with_think.model_dump()
        print("ACTION START")
        print(action_dict)
        action_with_think = ActionWithThinkB(**action_dict)

        return action_with_think

    async def generate_report(self, original_question: str) -> str:
        """Generate a report based on the collected knowledge"""
        current_date = self._get_current_date()

        # Create a list of visited URLs with their display ID instead of actual URL
        display_visited_urls = []

        for url in self.state.visited_urls:
            if url in self.state.all_urls:
                url_data = self.state.all_urls[url].copy()
                display_url = self.state.get_display_url(url)
                url_data["display_url"] = display_url
                url_data["original_url"] = url
                # Include the URL mapping in the title to make it visible in the report
                url_data["title"] = f"{url_data.get('title', 'No Title')}"
                # Use the display URL in the url field
                url_data["url"] = display_url
                display_visited_urls.append(url_data)

        stream = b.stream.GenerateReport(
            original_question=original_question,
            knowledge=self.state.knowledge_source.get_knowledge_by_types([
                KnowledgeType.QA,
                KnowledgeType.URL,
                KnowledgeType.Strategy,
                KnowledgeType.SearchInfo,
            ]),
            visited_urls=display_visited_urls,
            diary_context=self.state.diary_context,
            current_date=current_date,
            references=self.state.final_references,
        )

        async for partial in stream:
            if self.stream_event:
                await self.stream_event("writing_report", {"final_report": partial})
                await asyncio.sleep(0)

        report_output = await stream.get_final_response()
        return report_output

    async def _send_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send an event to the stream if the stream_event function is available"""
        if self.stream_event:
            await self.stream_event(event_type, data)
            await asyncio.sleep(0)

    async def _search_implementation(self, question: str, max_steps: int = 20) -> str:
        """
        Implementation of the search logic, separated to allow for timeout wrapping
        """
        # Reset state
        self._reset_state()
        self.state.question = question.strip()
        self.state.gaps = [question]  # All questions to be answered including the original question
        self.state.all_questions = [question]
        await self._send_event(Event.START.value, {"question": question, "max_steps": max_steps})
        while (self.state.total_step < max_steps and self.state.bad_attempts < self.config.max_bad_attempts):
            self.state.step += 1
            self.state.total_step += 1

            print(f"\n--- Step {self.state.step} ---")
            await self._send_event(
                Event.STEP.value,
                {
                    "step": self.state.step,
                    "total_step": self.state.total_step
                },
            )

            # Get the current question from the gaps
            self.state.allow_reflect = self.state.allow_reflect and (len(self.state.gaps) <= 1)

            self.state.current_question = (self.state.gaps.pop(0) if self.state.gaps else question)

            if self.state.current_question not in self.state.evaluation_metrics:
                self.state.evaluation_metrics[self.state.current_question] = await evaluate_question(
                    self.state.current_question)

            self.state.allow_search = self.state.allow_search and (len(
                get_unvisited_urls(self.state.all_urls, self.state.visited_urls)) < 50
                                                                  )  # disable search when too many urls already

            # Generate the next action
            action_with_think = await self.generate_action(self.state.current_question)

            # Extract the action
            action = action_with_think.action
            thinking = action_with_think.thinking

            print(f"Thinking: {thinking}...")

            actions_allowed = self.state.get_allowed_actions()
            actions_str = ", ".join(actions_allowed)

            print(f"{(type(action).__name__).lower()} <- [{actions_str}]")
            await self._send_event(
                Event.THINKING.value,
                {
                    "thinking": action_with_think.thinking,
                    "action": actions_str,
                },
            )

            self.state.reset_permissions()

            # Find the appropriate handler for the action type
            action_type = type(action)
            if action_type in self.handlers:
                await self.handlers[action_type].handle(action_with_think)

                if self.state.is_final:
                    break
            else:
                print(f"Unknown action type: {type(action)}")
                await self._send_event(
                    Event.ERROR.value,
                    {"message": f"Unknown action type: {type(action)}"},
                )
                self.state.bad_attempts += 1

            # Sleep between steps
            print(f"Step {self.state.step} completed.")
            await self._send_event(Event.STEP_COMPLETED.value, {"step": self.state.step})
            await self.sleep()

        if not self.state.is_final:
            self.state.step += 1
            self.state.total_step += 1
            self.state.is_final = True

        print("\n--- Generating final report ---")
        await self._send_event(Event.GENERATING_REPORT.value, {})
        final_report = await self.generate_report(question)

        await self._send_event(Event.COMPLETE.value, {"final_report": final_report})
        # Signal the end of the stream
        await asyncio.sleep(0.1)  # Small delay to ensure all events are processed

        return final_report

    async def search(self, question: str, max_steps: int = 20) -> str:
        """
        Execute a deep search for the given question

        Args:
            question: The question to search for
            max_steps: Maximum number of steps to take

        Returns:
            The final answer or report
        """
        # Set an overall timeout for the entire search process (10 minutes)
        try:
            return await asyncio.wait_for(
                self._search_implementation(question, max_steps),
                timeout=self.config.search_process_timeout,
            )
        except asyncio.TimeoutError:
            logging.warning("Global timeout for search question: %s", question)
            # Generate a partial report with what we have so far
            self.state.is_final = True
            report = await self.generate_report(question)
            await self._send_event(
                Event.COMPLETE.value,
                {"final_report": report},
            )
            return report
