import asyncio
import logging
import json

from pydantic import BaseModel
from typing import Any, Callable, Dict, List, Optional

from openai import OpenAI, AsyncOpenAI

from ii_researcher.reasoning.config import get_report_config
from ii_researcher.reasoning.models.trace import Trace
from ii_researcher.reasoning.tools.tool_history import ToolHistory


class Subtopics(BaseModel):
    subtopics: List[str]


class ReportBuilder:

    def __init__(self, stream_event: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        self.config = get_report_config()
        self.client = OpenAI(
            api_key=self.config.llm.api_key,
            base_url=self.config.llm.base_url,
        )
        self.async_client = AsyncOpenAI(
            api_key=self.config.llm.api_key,
            base_url=self.config.llm.base_url,
        )
        self.stream_event = stream_event

    def generate_report(self, trace: Trace) -> str:
        try:
            messages = self.config.generate_report_messages(trace.to_string(), trace.query)
            return self._generate_response(messages)

        except Exception as e:
            logging.error("Error generating report: %s", str(e))
            raise

    async def generate_report_stream(self, trace: Trace, callback: Optional[Callable[[str], None]] = None) -> str:
        """Generate a streaming report using the OpenAI API."""

        try:
            messages = self.config.generate_report_messages(trace.to_string(), trace.query)
            return await self._generate_stream(messages, callback)

        except Exception as e:
            logging.error("Error generating streaming report: %s", str(e))
            raise

    def generate_advance_report(self, tool_history: ToolHistory, trace: Trace) -> str:
        """Generate a comprehensive report from the research trace and tool history.

        Args:
            tool_history: History of tools used during research
            trace: The research trace containing the process and findings

        Returns:
            str: A complete report including introduction, subtopics, and references

        Raises:
            Exception: If any part of the report generation fails
        """
        try:
            logging.info("Starting advanced report generation")
            subtopics = self._generate_subtopics(trace)
            logging.info(f"Generated {len(subtopics)} subtopics")

            introduction = self._generate_introduction(trace)
            logging.info("Generated introduction")

            content_from_previous_subtopics = introduction
            for i, subtopic in enumerate(subtopics, 1):
                logging.info(f"Generating subtopic {i}/{len(subtopics)}: {subtopic}")
                subtopic_content = self._generate_subtopic_report(trace, subtopic, content_from_previous_subtopics,
                                                                  subtopics)
                content_from_previous_subtopics += f"\n\n{subtopic_content}"

            references = self._generate_references(tool_history)
            logging.info("Generated references")

            full_report = content_from_previous_subtopics + references
            logging.info("Completed advanced report generation")
            return full_report

        except Exception as e:
            logging.error("Error generating advance report: %s", str(e))
            raise

    async def generate_advance_report_stream(
        self,
        tool_history: ToolHistory,
        trace: Trace,
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        try:
            subtopics = await self._generate_subtopics_stream(trace)
            introduction = await self._generate_introduction_stream(trace, callback)
            content_from_previous_subtopics = introduction
            for subtopic in subtopics:
                subtopic_content = await self._generate_subtopic_report_stream(trace, subtopic,
                                                                               content_from_previous_subtopics,
                                                                               subtopics, callback)
                content_from_previous_subtopics += f"\n\n{subtopic_content}"
            references = await self._generate_references_stream(tool_history, callback)
            full_report = content_from_previous_subtopics + references
            return full_report

        except Exception as e:
            logging.error("Error generating advance report: %s", str(e))
            raise

    async def _generate_introduction_stream(self,
                                            trace: Trace,
                                            callback: Optional[Callable[[str], None]] = None) -> str:
        try:
            messages = self.config.generate_introduction_messages(trace.to_string(), trace.query)
            logging.info(f"Generating introduction")
            return await self._generate_stream(messages, callback)
        except Exception as e:
            logging.error("Error generating introduction: %s", str(e))
            raise

    async def _generate_subtopics_stream(self, trace: Trace) -> List[str]:
        try:
            messages = self.config.generate_subtopics_messages(trace.to_string(), trace.query)
            response = await self.async_client.beta.chat.completions.parse(model=self.config.llm.report_model,
                                                                           messages=messages,
                                                                           temperature=self.config.llm.temperature,
                                                                           top_p=self.config.llm.top_p,
                                                                           response_format=Subtopics)
            subtopics = response.choices[0].message.parsed.subtopics
            logging.info(f"Subtopics: {json.dumps(subtopics)}")
            return subtopics
        except Exception as e:
            logging.error("Error generating subtopics: %s", str(e))
            raise

    async def _generate_subtopic_report_stream(self,
                                               trace: Trace,
                                               current_subtopic: str,
                                               content_from_previous_subtopics: str,
                                               subtopics: list[str],
                                               callback: Optional[Callable[[str], None]] = None) -> str:
        try:
            messages = self.config.generate_subtopic_report_messages(trace.to_string(), content_from_previous_subtopics,
                                                                     subtopics, current_subtopic, trace.query)
            logging.info(f"Generating subtopic report: {current_subtopic}")
            return await self._generate_stream(messages, callback)
        except Exception as e:
            logging.error("Error generating subtopic report: %s", str(e))
            raise

    def _generate_references(self, tool_history: ToolHistory) -> str:
        try:
            url_markdown = "\n\n\n## References\n\n"
            url_markdown += "".join(f"- [{url}]({url})\n" for url in tool_history.get_visited_urls())
            url_markdown += "".join(f"- [{query}]({query})\n" for query in tool_history.get_searched_queries())
            return url_markdown
        except Exception as e:
            logging.error("Error generating references: %s", str(e))
            raise

    async def _generate_references_stream(
        self,
        tool_history: ToolHistory,
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Generate the references section of the report with streaming.

        Args:
            tool_history: History of tools used containing URLs and queries
            callback: Optional callback for streaming tokens

        Returns:
            str: The references section text

        Raises:
            Exception: If references generation fails
        """
        try:
            url_markdown = "\n\n\n## References\n\n"
            if self.stream_event:
                await self.stream_event("writing_report", {"final_report": url_markdown})
                await asyncio.sleep(0)

            # Stream URLs
            for url in tool_history.get_visited_urls().union(tool_history.get_searched_queries()):
                ref_line = f"- [{url}]({url})\n"
                url_markdown += ref_line
                if callback:
                    callback(ref_line)
                if self.stream_event:
                    await self.stream_event("writing_report", {"final_report": url_markdown})
                    await asyncio.sleep(0)
            return url_markdown
        except Exception as e:
            logging.error("Error generating references stream: %s", str(e))
            raise

    async def _generate_stream(
        self,
        messages: List[Dict[str, Any]],
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        stream = await self.async_client.chat.completions.create(
            model=self.config.llm.report_model,
            messages=messages,
            temperature=self.config.llm.temperature,
            top_p=self.config.llm.top_p,
            stream=True,
        )

        full_content = ""
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content

                if callback:
                    callback(content)

                if self.stream_event:
                    await self.stream_event("writing_report", {"final_report": full_content})
                    await asyncio.sleep(0)

        return full_content

    def _generate_response(self, messages: List[Dict[str, Any]]) -> str:
        response = self.client.chat.completions.create(
            model=self.config.llm.report_model,
            messages=messages,
            temperature=self.config.llm.temperature,
            top_p=self.config.llm.top_p,
        )

        return response.choices[0].message.content

    def _generate_introduction(self, trace: Trace) -> str:
        """Generate the introduction section of the report.

        Args:
            trace: The research trace containing the process and findings

        Returns:
            str: The introduction text

        Raises:
            Exception: If introduction generation fails
        """
        try:
            messages = self.config.generate_introduction_messages(trace.to_string(), trace.query)
            return self._generate_response(messages)
        except Exception as e:
            logging.error("Error generating introduction: %s", str(e))
            raise

    def _generate_subtopics(self, trace: Trace) -> List[str]:
        """Generate a list of subtopics for the report.

        Args:
            trace: The research trace containing the process and findings

        Returns:
            List[str]: List of subtopics to cover in the report

        Raises:
            Exception: If subtopics generation fails
        """
        try:
            messages = self.config.generate_subtopics_messages(trace.to_string(), trace.query)
            response = self.client.beta.chat.completions.parse(model=self.config.llm.report_model,
                                                               messages=messages,
                                                               temperature=self.config.llm.temperature,
                                                               top_p=self.config.llm.top_p,
                                                               response_format=Subtopics)
            subtopics = response.choices[0].message.parsed.subtopics
            return subtopics
        except Exception as e:
            logging.error("Error generating subtopics: %s", str(e))
            raise

    def _generate_subtopic_report(self, trace: Trace, current_subtopic: str, content_from_previous_subtopics: str,
                                  subtopics: List[str]) -> str:
        """Generate the report content for a specific subtopic.

        Args:
            trace: The research trace containing the process and findings
            current_subtopic: The subtopic to generate content for
            content_from_previous_subtopics: Content generated so far
            subtopics: List of all subtopics in the report

        Returns:
            str: The generated content for the subtopic

        Raises:
            Exception: If subtopic content generation fails
        """
        try:
            messages = self.config.generate_subtopic_report_messages(trace.to_string(), content_from_previous_subtopics,
                                                                     subtopics, current_subtopic, trace.query)
            return self._generate_response(messages)
        except Exception as e:
            logging.error("Error generating subtopic report: %s", str(e))
            raise
