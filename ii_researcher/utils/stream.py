import asyncio
import json
import time
from typing import Any, Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EventMessage:
    """Container for streaming event messages"""

    event_type: str
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for streaming"""
        return {
            "type": self.event_type,
            "data": self.data,
            "timestamp": datetime.now().timestamp(),
        }


class StreamManager:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def create_event_message(self, event_type: str, data: Dict[str, Any]):
        event_message = EventMessage(event_type=event_type, data=data)
        event = event_message.to_dict()
        await self.queue.put(event)

    def create_error_event(self, error_message: str) -> str:
        error_event = {
            "type": "error",
            "data": {"message": error_message},
            "timestamp": time.time(),
        }
        return f"data: {json.dumps(error_event)}\n\n"

    def create_complete_event(self, final_report: Any) -> str:
        complete_event = {
            "type": "complete",
            "data": {"final_report": final_report},
            "timestamp": time.time(),
        }
        return f"data: {json.dumps(complete_event)}\n\n"

    def create_close_event(self) -> str:
        close_event = {
            "type": "stream_closed",
            "data": {"reason": "Connection closed"},
            "timestamp": time.time(),
        }
        return f"data: {json.dumps(close_event)}\n\n"
