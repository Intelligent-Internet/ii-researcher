import asyncio
import logging

from baml_client.async_client import b
from baml_client.types import KnowledgeItem, KnowledgeType, Search
from ii_researcher_legacy.ii_researcher.config import SEARCH_PROVIDER, SEARCH_QUERY_TIMEOUT
from ii_researcher_legacy.ii_researcher.events import Event
from ii_researcher_legacy.ii_researcher.pipeline.action_handler.base import ActionHandler
from ii_researcher_legacy.ii_researcher.pipeline.schemas import ActionWithThinkB
from ii_researcher_legacy.ii_researcher.tool_clients.search_client import SearchClient
from ii_researcher_legacy.ii_researcher.utils.prompt import SEARCH_DUPLICATE_PROMPT, SEARCH_SUCCESS_PROMPT
from ii_researcher_legacy.ii_researcher.utils.text_tools import choose_k
from ii_researcher_legacy.ii_researcher.utils.url_tools import normalize_url


class SearchHandler(ActionHandler):

    async def handle(self, action_with_think: ActionWithThinkB) -> None:
        """Handle a search action"""
        assert isinstance(action_with_think.action, Search)
        action = action_with_think.action

        # Get unique search queries after deduplication
        unique_queries = await self._get_unique_search_queries(action.search_requests, action_with_think.thinking)

        # If no unique queries after deduplication, log and disable search
        if not unique_queries:
            self._log_duplicate_search(unique_queries)
            self.state.allow_search = False
            return

        # Process search queries and collect results
        results = await self._process_search_queries(unique_queries)

        # Handle search results
        if not results:
            self._log_duplicate_search(unique_queries)
            self.state.allow_search = False
        else:
            await self._handle_search_results(unique_queries, results)

    async def _get_unique_search_queries(self, search_requests, thinking):
        """Get unique search queries after deduplication and rewriting"""
        # Deduplicate search requests
        dedup_result = await b.DedupQueries(new_queries=search_requests, existing_queries=[])
        search_requests = choose_k(dedup_result.unique_queries, self.state.config.max_queries_per_step)

        if not search_requests:
            return []

        # Rewrite queries
        current_date = self._get_current_date()
        tasks = [b.RewriteQuery(
            query=query,
            think=thinking,
            current_date=current_date,
        ) for query in search_requests]

        rewrite_result = await asyncio.gather(*tasks)
        keywords_queries = [query for result in rewrite_result for query in result.queries]

        # Deduplicate against existing keywords
        dedup_result = await b.DedupQueries(new_queries=keywords_queries, existing_queries=self.state.all_keywords)

        # Return top K unique queries
        return choose_k(dedup_result.unique_queries, self.state.config.max_queries_per_step)

    async def _process_search_queries(self, queries):
        """Process search queries and return results"""
        if not queries:
            return []

        await self._send_event(Event.SEARCH.value, {"queries": queries})
        tasks = [self._process_single_query(query) for query in queries]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    async def _process_single_query(self, query):
        """Process a single search query"""
        logging.info("Search query: %s", query)

        try:
            search_tool = SearchClient(
                query=query,
                max_results=self.state.config.max_website_per_query,
                search_provider=SEARCH_PROVIDER,
            )

            # Add a timeout for the search operation
            try:
                results = await asyncio.wait_for(
                    asyncio.to_thread(search_tool.search),
                    timeout=SEARCH_QUERY_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logging.warning("Search timeout for query: %s", query)
                return None

            if len(results) == 0:
                raise Exception("No results found")

            # Process results
            min_results = self._process_search_results(results, query)

            # Add query to keywords
            self.state.all_keywords.append(query)

            return min_results

        except Exception as error:
            logging.warning("%s search failed for query %s: %s", SEARCH_PROVIDER, query, error)
            return None
        finally:
            await self.sleep()

    def _process_search_results(self, results, query):
        """Process search results and update state"""
        min_results = []
        for r in results:
            result = {
                "title": r.get("title", ""),
                "url": normalize_url(r.get("url", r.get("href", ""))),
                "description": r.get("description", r.get("content", "")),
                "query": query,
            }
            min_results.append(result)

            # Add result to URL mapping
            self.state.all_urls[result["url"]] = result

        return min_results

    async def _handle_search_results(self, queries, results):
        """Handle search results"""
        flattened_results = [item for sublist in results for item in sublist]

        await self._send_event(
            Event.SEARCH_RESULTS.value,
            {"results": flattened_results},
        )

        # Add search info to knowledge
        for query, result_set in zip(queries, results):
            if result_set:
                await self._add_search_knowledge(query, result_set)

        # Log success to diary
        step_diary = SEARCH_SUCCESS_PROMPT.format(
            step=self.state.step,
            current_question=self.state.current_question,
            keywords=", ".join(queries),
        )
        self._add_to_diary(step_diary)

    async def _add_search_knowledge(self, query, results):
        """Add search results to knowledge base"""
        if not results:
            return

        description_text = (
            "\n\n ".join(
                [f"{self.state.get_display_url(r.get('url', ''))}: {r.get('description', '')}" for r in results]) +
            "\n\nBut this is just a quick look, you need to visit the websites to get more details if needed.")

        await self._add_to_knowledge(
            KnowledgeItem(
                question=f'What do Internet say about "{query}"?',
                answer=description_text,
                type=KnowledgeType.SearchInfo,
                updated=self._get_current_date(),
            ))

    def _log_duplicate_search(self, queries):
        """Log duplicate search or failed search to diary"""
        step_diary = SEARCH_DUPLICATE_PROMPT.format(
            step=self.state.step,
            current_question=self.state.current_question,
            keywords=", ".join(queries),
        )
        self._add_to_diary(step_diary)
        self.state.allow_search = False
