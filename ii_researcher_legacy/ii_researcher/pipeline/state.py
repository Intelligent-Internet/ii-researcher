from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ii_researcher_legacy.baml_client.types import EvaluationType, KnowledgeItem, KnowledgeType
from ii_researcher_legacy.ii_researcher.pipeline.schemas import Reference, SearchResult  # noqa


@dataclass
class KnowledgeSource:
    all_knowledge: List[KnowledgeItem] = field(default_factory=list)

    def add_knowledge(self, knowledge: KnowledgeItem) -> None:
        """Add a knowledge item to the knowledge base"""
        self.all_knowledge.append(knowledge)

    def get_knowledge(self) -> List[KnowledgeItem]:
        """Get the knowledge base"""
        return self.all_knowledge

    def get_knowledge_by_types(self, types: List[KnowledgeType]) -> List[KnowledgeItem]:
        """Get the knowledge base by types"""
        return [knowledge for knowledge in self.all_knowledge if knowledge.type in types]


@dataclass
class AgentState:
    """Container for the agent's state"""

    all_keywords: List[str] = field(default_factory=list)
    knowledge_source: KnowledgeSource = field(default_factory=KnowledgeSource)
    all_questions: List[str] = field(default_factory=list)
    diary_context: List[str] = field(default_factory=list)
    all_urls: Dict[str, dict] = field(default_factory=dict)
    visited_urls: List[str] = field(default_factory=list)
    evaluation_metrics: Dict[str, List[EvaluationType]] = field(default_factory=dict)
    bad_context: List[Dict[str, Any]] = field(default_factory=list)
    final_references: List[Reference] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    # URL mapping dictionary to track URL IDs
    url_id_mapping: Dict[str, int] = field(default_factory=dict)

    # Agent permissions
    allow_reflect: bool = True
    allow_read: bool = True
    allow_answer: bool = True
    allow_search: bool = True

    bad_attempts: int = 0
    total_step: int = 0
    step: int = 0
    is_final: bool = False
    current_question: str = ""
    question: str = ""

    def reset(self) -> None:
        """Reset all state"""
        self.all_keywords = []
        self.knowledge_source = KnowledgeSource()
        self.all_questions = []
        self.diary_context = []
        self.all_urls = {}
        self.visited_urls = []
        self.evaluation_metrics = {}
        self.bad_context = []
        self.final_references = []
        self.gaps = []
        self.url_id_mapping = {}

        # Reset permissions
        self.reset_permissions()

        self.bad_attempts = 0
        self.total_step = 0
        self.step = 0
        self.is_final = False
        self.current_question = ""
        self.question = ""

    def reset_permissions(self) -> None:
        """Reset all permissions to True"""
        self.allow_reflect = True
        self.allow_read = True
        self.allow_answer = True
        self.allow_search = True

    def get_permissions_as_dict(self) -> Dict[str, bool]:
        """Return permissions as dictionary"""
        return {
            "allow_reflect": self.allow_reflect,
            "allow_read": self.allow_read,
            "allow_answer": self.allow_answer,
            "allow_search": self.allow_search,
        }

    def get_allowed_actions(self) -> List[str]:
        """Get list of allowed actions as strings"""
        allowed = []
        if self.allow_search:
            allowed.append("search")
        if self.allow_read:
            allowed.append("read")
        if self.allow_answer:
            allowed.append("answer")
        if self.allow_reflect:
            allowed.append("reflect")
        return allowed

    def get_url_id(self, url: str) -> str:
        """Get a normalized ID for a URL (<url-n> format)"""
        if url not in self.url_id_mapping:
            # Assign a new ID (1-indexed)
            new_id = len(self.url_id_mapping) + 1
            self.url_id_mapping[url] = new_id

        return f"<url-{self.url_id_mapping[url]}>"

    def get_display_url(self, url: str) -> str:
        """Get a display version of a URL, using the [Title](<url-n>) format"""
        return (f"[{self.all_urls[url].get('title', 'No Title')}]({self.get_url_id(url)})")

    def get_url_mapping(self) -> Dict[str, str]:
        """Return mapping of URL IDs to actual URLs"""
        return {f"<url-{id}>": url for url, id in self.url_id_mapping.items()}

    def get_actual_url(self, url: str) -> str:
        """Convert a display URL (<url-n>) back to the actual URL
        If the input is already an actual URL, return it unchanged.
        """
        # Check if this is a display URL format
        if url.startswith("<url-") and url.endswith(">"):
            # Look through the reverse mapping
            for actual_url, id_value in self.url_id_mapping.items():
                if url == f"<url-{id_value}>":
                    return actual_url
        # If not found or not in display format, return the original
        return url


@dataclass
class ActionState:
    """
    A wrapper around AgentState that provides action handlers with access to the agent's state
    and additional configuration needed by handlers.
    """

    agent_state: AgentState
    config: Any = None
    stream_event: Optional[Callable[[str, Dict[str, Any]], None]] = None

    # Property proxies that forward access to the underlying agent state
    @property
    def all_keywords(self) -> List[str]:
        return self.agent_state.all_keywords

    @property
    def knowledge_source(self) -> KnowledgeSource:
        return self.agent_state.knowledge_source

    @property
    def all_questions(self) -> List[str]:
        return self.agent_state.all_questions

    @property
    def diary_context(self) -> List[str]:
        return self.agent_state.diary_context

    @property
    def all_urls(self) -> Dict[str, dict]:
        return self.agent_state.all_urls

    @property
    def visited_urls(self) -> List[str]:
        return self.agent_state.visited_urls

    @property
    def evaluation_metrics(self) -> Dict[str, List[EvaluationType]]:
        return self.agent_state.evaluation_metrics

    @property
    def bad_context(self) -> List[Dict[str, Any]]:
        return self.agent_state.bad_context

    @property
    def final_references(self) -> List[Reference]:
        return self.agent_state.final_references

    @final_references.setter
    def final_references(self, value: List[Reference]) -> None:
        self.agent_state.final_references = value

    @property
    def gaps(self) -> List[str]:
        return self.agent_state.gaps

    @property
    def url_id_mapping(self) -> Dict[str, int]:
        return self.agent_state.url_id_mapping

    @property
    def allow_reflect(self) -> bool:
        return self.agent_state.allow_reflect

    @allow_reflect.setter
    def allow_reflect(self, value: bool) -> None:
        self.agent_state.allow_reflect = value

    @property
    def allow_read(self) -> bool:
        return self.agent_state.allow_read

    @allow_read.setter
    def allow_read(self, value: bool) -> None:
        self.agent_state.allow_read = value

    @property
    def allow_answer(self) -> bool:
        return self.agent_state.allow_answer

    @allow_answer.setter
    def allow_answer(self, value: bool) -> None:
        self.agent_state.allow_answer = value

    @property
    def allow_search(self) -> bool:
        return self.agent_state.allow_search

    @allow_search.setter
    def allow_search(self, value: bool) -> None:
        self.agent_state.allow_search = value

    @property
    def bad_attempts(self) -> int:
        return self.agent_state.bad_attempts

    @bad_attempts.setter
    def bad_attempts(self, value: int) -> None:
        self.agent_state.bad_attempts = value

    @property
    def total_step(self) -> int:
        return self.agent_state.total_step

    @total_step.setter
    def total_step(self, value: int) -> None:
        self.agent_state.total_step = value

    @property
    def step(self) -> int:
        return self.agent_state.step

    @step.setter
    def step(self, value: int) -> None:
        self.agent_state.step = value

    @property
    def is_final(self) -> bool:
        return self.agent_state.is_final

    @is_final.setter
    def is_final(self, value: bool) -> None:
        self.agent_state.is_final = value

    @property
    def current_question(self) -> str:
        return self.agent_state.current_question

    @current_question.setter
    def current_question(self, value: str) -> None:
        self.agent_state.current_question = value

    @property
    def question(self) -> str:
        return self.agent_state.question

    @question.setter
    def question(self, value: str) -> None:
        self.agent_state.question = value

    def reset(self) -> None:
        """Reset the underlying agent state"""
        self.agent_state.reset()

    def reset_permissions(self) -> None:
        """Reset all permissions to True in the underlying agent state"""
        self.agent_state.reset_permissions()

    def get_permissions_as_dict(self) -> Dict[str, bool]:
        """Return permissions as dictionary from the underlying agent state"""
        return self.agent_state.get_permissions_as_dict()

    def get_allowed_actions(self) -> List[str]:
        """Get list of allowed actions as strings from the underlying agent state"""
        return self.agent_state.get_allowed_actions()

    def get_url_id(self, url: str) -> str:
        """Get a normalized ID for a URL from the underlying agent state"""
        return self.agent_state.get_url_id(url)

    def get_display_url(self, url: str) -> str:
        """Get a display version of a URL from the underlying agent state"""
        return self.agent_state.get_display_url(url)

    def get_url_mapping(self) -> Dict[str, str]:
        """Return mapping of URL IDs to actual URLs from the underlying agent state"""
        return self.agent_state.get_url_mapping()

    def get_actual_url(self, url: str) -> str:
        """Convert a display URL to actual URL using the underlying agent state"""
        return self.agent_state.get_actual_url(url)
