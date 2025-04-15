import asyncio
import logging
from typing import Any, Dict

from ii_researcher_legacy.baml_client.async_client import b
from ii_researcher_legacy.baml_client.types import KnowledgeItem, KnowledgeType, Visit
from ii_researcher_legacy.ii_researcher.events import Event
from ii_researcher_legacy.ii_researcher.pipeline.action_handler.base import ActionHandler
from ii_researcher_legacy.ii_researcher.pipeline.schemas import ActionWithThinkB
from ii_researcher_legacy.ii_researcher.tool_clients.scrape_client import ScrapeClient
from ii_researcher_legacy.ii_researcher.utils.prompt import (
    VISIT_DUPLICATE_PROMPT,
    VISIT_FAIL_PROMPT,
    VISIT_SUCCESS_PROMPT,
)
from ii_researcher_legacy.ii_researcher.utils.text_tools import choose_k, remove_all_line_breaks
from ii_researcher_legacy.ii_researcher.utils.url_tools import normalize_url


class VisitHandler(ActionHandler):

    async def handle(self, action_with_think: ActionWithThinkB) -> None:
        """Handle a visit action"""
        assert isinstance(action_with_think.action, Visit)
        action = action_with_think.action

        # Convert any display URLs to actual URLs
        actual_urls = [self.state.get_actual_url(url) for url in action.urls]

        # Normalize URLs and filter out already visited ones
        normalized_urls = [normalize_url(url) for url in actual_urls]
        unvisited_urls = [url for url in normalized_urls if url not in self.state.visited_urls]

        top_k_unvisited_urls = choose_k(unvisited_urls, self.state.config.max_urls_per_step)

        if len(top_k_unvisited_urls) > 0:
            url_ids = [self.state.get_url_id(url) for url in top_k_unvisited_urls]
            # await self._send_event(Event.VISIT.value, {"urls": display_urls})

            # Process the actual URLs
            url_results = await asyncio.gather(*[self._handle_url(url) for url in top_k_unvisited_urls])

            # Check if we've found useful information
            success = any(r and r.get("result", {}).get("content", "").strip() for r in url_results)

            await self._send_event(Event.VISIT.value, {"urls": url_ids, "results": url_results})
            if success:
                # Use display URLs in the diary entry
                diary_entries = []
                for r in url_results:
                    if r and r.get("url", "") in self.state.all_urls:
                        diary_entries.append(self.state.get_display_url(r.get("url", "")))

                self._add_to_diary(
                    VISIT_SUCCESS_PROMPT.format(
                        step=self.state.step,
                        diary_entries=chr(10).join(diary_entries),
                    ))
            else:
                self._add_to_diary(VISIT_FAIL_PROMPT.format(
                    step=self.state.step,
                ))
        else:
            self._add_to_diary(VISIT_DUPLICATE_PROMPT.format(
                step=self.state.step,
            ))

    async def _handle_url(self, url: str) -> Dict[str, Any]:
        """Handle a URL"""
        response = {}
        try:
            display_url = self.state.get_display_url(url)

            scrape_tool = ScrapeClient(query=self.state.all_urls[url]["query"])

            try:
                response = await asyncio.wait_for(
                    scrape_tool.scrape(url),
                    timeout=self.state.config.scrape_url_timeout,
                )
                response.pop("raw_content", None)

                url_knowledge = KnowledgeItem(
                    question=f"What is in {display_url} ?",
                    answer=remove_all_line_breaks(response.get("content", "")),
                    references=[display_url],
                    type=KnowledgeType.URL,
                    updated=self._get_current_date(),
                )
                await self._add_to_knowledge(url_knowledge)

                critic = await b.AnalyzeCritic(
                    knowledges=[url_knowledge],
                    context=self.state.diary_context,
                    question=self.state.question,
                )

                await self._add_to_knowledge(
                    KnowledgeItem(
                        question=f"What is knowledge gain from {display_url}, what is next strategy?",
                        answer=critic,
                        type=KnowledgeType.Strategy,
                        updated=self._get_current_date(),
                    ))

            except asyncio.TimeoutError:
                logging.warning('Timeout when visiting URL "%s"', display_url)
                response = {
                    "url": url,
                    "content": f"Error: Timeout when visiting URL {display_url}. Ignore this URL.",
                }

        except (ValueError, KeyError, AttributeError) as error:
            display_url = self.state.get_display_url(url)
            logging.warning('Error visiting URL "%s": %s', display_url, error)
            response = {
                "url": url,
                "content": f"Error visiting URL {display_url}: {error}",
            }
        finally:
            self._add_to_visited_urls(url)

        return {"url": url, "result": response}

    def _add_to_visited_urls(self, url: str) -> None:
        """Add a URL to the visited URLs list"""
        normalized_url = normalize_url(url)
        if normalized_url not in self.state.visited_urls:
            self.state.visited_urls.append(normalized_url)
