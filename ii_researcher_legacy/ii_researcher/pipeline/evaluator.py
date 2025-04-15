import asyncio
from datetime import datetime
from typing import List

from baml_client.async_client import b
from baml_client.types import Answer, EvaluationType
from ii_researcher_legacy.ii_researcher.config import SCRAPE_URL_TIMEOUT
from ii_researcher_legacy.ii_researcher.pipeline.schemas import (
    AttributionAnalysis,
    CompletenessAnalysis,
    EvaluationResponse,
    FreshnessAnalysis,
    PluralityAnalysis,
)
from ii_researcher_legacy.ii_researcher.tool_clients.scrape_client import ScrapeClient


async def evaluate_answer(
    question: str,
    action: Answer,
    evaluation_types: List[EvaluationType],
    visited_urls: List[str],
) -> EvaluationResponse:
    # Only add attribution if we have valid references
    urls = []
    if action.references:
        urls = [ref.url for ref in action.references if ref.url.startswith("http") and ref.url not in visited_urls]

    unique_new_urls = list(set(urls))

    if len(unique_new_urls) > 0:
        evaluation_types = [EvaluationType.Attribution] + evaluation_types

    # QUICKFIX: remove freshness and plurality for now
    excluded_types = {EvaluationType.Freshness, EvaluationType.Plurality}
    evaluation_types = [t for t in evaluation_types if t not in excluded_types]

    pass_reason = ""
    result = None
    for evaluation_type in evaluation_types:
        if evaluation_type == EvaluationType.Attribution:
            # Safely handle references and ensure we have content
            all_knowledge = await fetch_source_content(unique_new_urls, question=question)

            visited_urls.extend(unique_new_urls)

            if not all_knowledge.strip():
                return EvaluationResponse(
                    pass_evaluation=False,
                    think=
                    f"The answer does provide URL references {unique_new_urls}, but the content could not be fetched or is empty. Need to found some other references and URLs",
                    type=EvaluationType.Attribution,
                )
            result = await b.EvaluateAttribution(
                question=question,
                answer=action.answer_text,
                source_content=all_knowledge,
            )

            result = EvaluationResponse(
                pass_evaluation=result.pass_evaluation,
                think=result.think,
                type=EvaluationType.Attribution,
                attribution_analysis=AttributionAnalysis(
                    sources_provided=result.sources_provided,
                    sources_verified=result.sources_verified,
                    quotes_accurate=result.quotes_accurate,
                ),
            )

        elif evaluation_type == EvaluationType.Definitive:
            result = await b.EvaluateDefinitive(
                question=question,
                answer=action.answer_text,
            )
            result = EvaluationResponse(
                pass_evaluation=result.pass_evaluation,
                think=result.think,
                type=EvaluationType.Definitive,
            )

        elif evaluation_type == EvaluationType.Freshness:
            result = await b.EvaluateFreshness(
                question=question,
                answer=action.answer_text,
                current_time=datetime.now().strftime("%Y-%m-%d"),
            )
            result = EvaluationResponse(
                pass_evaluation=result.pass_evaluation,
                think=result.think,
                type=EvaluationType.Freshness,
                freshness_analysis=FreshnessAnalysis(
                    days_ago=result.days_ago,
                    max_age_days=result.max_age_days,
                ),
            )

        elif evaluation_type == EvaluationType.Plurality:
            result = await b.EvaluatePlurality(
                question=question,
                answer=action.answer_text,
            )
            result = EvaluationResponse(
                pass_evaluation=result.pass_evaluation,
                think=result.think,
                type=EvaluationType.Plurality,
                plurality_analysis=PluralityAnalysis(
                    count_expected=result.count_expected,
                    count_provided=result.count_provided,
                ),
            )

        elif evaluation_type == EvaluationType.Completeness:
            result = await b.EvaluateCompleteness(
                question=question,
                answer=action.answer_text,
            )
            result = EvaluationResponse(
                pass_evaluation=result.pass_evaluation,
                think=result.think,
                type=EvaluationType.Completeness,
                completeness_analysis=CompletenessAnalysis(
                    aspects_expected=result.aspects_expected,
                    aspects_provided=result.aspects_provided,
                ),
            )

        # one failed evaluation, return the result immediately
        if result is not None:
            if not result.pass_evaluation:
                return result
            pass_reason += f"{result.think}\n\n"

    return EvaluationResponse(
        pass_evaluation=True,
        think=pass_reason,
        type=None,
    )


async def evaluate_question(
    question: str,
) -> List[EvaluationType]:
    result = await b.EvaluateQuestion(
        question=question,
    )
    types: List[EvaluationType] = [EvaluationType.Definitive]

    if result.needsFreshness:
        types.append(EvaluationType.Freshness)
    if result.needsPlurality:
        types.append(EvaluationType.Plurality)
    if result.needsCompleteness:
        types.append(EvaluationType.Completeness)
    return types


async def fetch_source_content(urls: List[str], question: str) -> str:
    """
    Fetches and combines content from multiple source URLs.

    Args:
        urls: List of URLs to fetch content from
        question: Question to use for compression

    Returns:
        Combined content from all sources as a string
    """
    if not urls:
        return ""

    scrape_tool = ScrapeClient(query=question)

    async def scrape(url):
        try:
            response = await asyncio.wait_for(scrape_tool.scrape(url), timeout=SCRAPE_URL_TIMEOUT)
            return response["content"]
        except asyncio.TimeoutError:
            return "Timeout for URL: " + url
        except Exception as e:
            return "Error for URL: " + url + " - " + str(e)

    tasks = [scrape(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return "\n\n".join([content for content in results if content.strip()])
