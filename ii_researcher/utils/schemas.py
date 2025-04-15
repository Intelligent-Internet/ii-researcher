from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field

from baml_client.types import (
    ActionWithThink,
    AlternativeSearchResult,
    EvaluationType,
    StandardSearchResult,
)
class ActionWithThinkB(ActionWithThink):
    is_final: bool | None = None


class Reference(BaseModel):
    exactQuote: str = Field(
        ...,
        description="Exact relevant quote from the document, must be a soundbite, short and to the point, no fluff",
    )
    url: str = Field(description="source URL; must be directly from the context", default="")
    title: Optional[str] = Field(None, description="Title of the document, if available")


class FreshnessAnalysis(BaseModel):
    days_ago: Optional[int] = None
    max_age_days: Optional[int] = None


class PluralityAnalysis(BaseModel):
    count_expected: Optional[int] = None
    count_provided: Optional[int] = None


class AttributionAnalysis(BaseModel):
    sources_provided: bool
    sources_verified: bool
    quotes_accurate: bool


class CompletenessAnalysis(BaseModel):
    aspects_expected: str
    aspects_provided: str


class EvaluationResponse(BaseModel):
    pass_evaluation: (
        bool  # 'pass' is a reserved keyword in Python, using pass_evaluation instead
    )
    think: str
    type: Optional[EvaluationType]
    freshness_analysis: Optional[FreshnessAnalysis] = None
    plurality_analysis: Optional[PluralityAnalysis] = None
    attribution_analysis: Optional[AttributionAnalysis] = None
    completeness_analysis: Optional[CompletenessAnalysis] = None


SearchResult = Union[StandardSearchResult, AlternativeSearchResult]


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
