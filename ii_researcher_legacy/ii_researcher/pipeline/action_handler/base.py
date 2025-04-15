import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

from ii_researcher_legacy.baml_client.types import KnowledgeItem
from ii_researcher_legacy.ii_researcher.events import Event
from ii_researcher_legacy.ii_researcher.pipeline.schemas import ActionWithThinkB
from ii_researcher_legacy.ii_researcher.pipeline.state import ActionState


class ActionHandler(ABC):

    def __init__(self, state: ActionState):
        """
        Initialize the action handler with the given state.
        This state is shared with the agent and all action handlers.
        """
        self.state = state

    @abstractmethod
    async def handle(self, action_with_think: ActionWithThinkB) -> None:
        """
        Handle the given action

        Args:
            action_with_think: The action to handle with its thinking
        """

    def _get_current_date(self) -> str:
        """Get the current date in YYYY-MM-DD HH:MM:SS format"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _add_to_diary(self, entry: str) -> None:
        """Add an entry to the diary context"""
        self.state.diary_context.append(entry)

    async def _add_to_knowledge(self, item: KnowledgeItem) -> None:
        """Add a knowledge item to the knowledge base"""
        self.state.knowledge_source.add_knowledge(item)
        await self._send_event(Event.KNOWLEDGE.value, item.model_dump())

    async def _send_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send an event to the stream if the stream_event function is available"""
        if self.state.stream_event:
            await self.state.stream_event(event_type, data)

    async def sleep(self) -> None:
        """Sleep for the specified number of milliseconds."""
        seconds = self.state.config.step_sleep_ms / 1000
        print(f"Waiting {seconds:.1f}s...")
        await asyncio.sleep(seconds)
