from enum import Enum


class Event(Enum):
    START = "start"  # When the process starts
    STEP = "step"  # When a step is started
    STEP_COMPLETED = "step_completed"  # When a step is completed
    THINKING = "thinking"  # When thinking is started
    KNOWLEDGE = "knowledge"  # When knowledge is added
    SEARCH = "search"  # When performing a search query
    SEARCH_RESULTS = "search_results"  # When search results are available
    VISIT = "visit"  # When visiting/scraping a URL
    REFLECT = "reflect"  # When analyzing gathered information
    ANSWER = "answer"  # When generating an answer
    ERROR = "error"  # When an error occurs
    COMPLETE = "complete"  # When the process is complete
    GENERATING_REPORT = "generating_report"  # When generating the final report
    DRAFT_ANSWER = "draft_answer"  # When generating a draft answer
    EVAL_ANSWER = "eval_answer"  # When evaluating the answer
