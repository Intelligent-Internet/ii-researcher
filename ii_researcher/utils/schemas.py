from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


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
