import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI, OpenAI

from ii_researcher.reasoning.config import get_config
from ii_researcher.reasoning.models.trace import Trace
from ii_researcher.reasoning.tools.registry import format_tool_descriptions


class OpenAIClient:
    """OpenAI API client."""

    def __init__(self):
        """Initialize the OpenAI client."""
        self.config = get_config()

        # Create synchronous client
        self.client = OpenAI(
            api_key=self.config.llm.api_key,
            base_url=self.config.llm.base_url,
        )

        # Create async client
        self.async_client = AsyncOpenAI(
            api_key=self.config.llm.api_key,
            base_url=self.config.llm.base_url,
        )

    def _get_messages(
        self, trace: Trace, instructions: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get the messages for the OpenAI API."""

        available_tools = format_tool_descriptions()
        system_prompt = self.config.system_prompt.format(
            available_tools=available_tools,
            current_date=datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": trace.query},
            {
                "role": "assistant",
                "content": trace.to_string(instructions),
                "prefix": True,
            },
        ]
        return messages

    def generate_completion(
        self, trace: Trace, instructions: Optional[str] = None
    ) -> Any:
        """Generate a completion using the OpenAI API."""
        messages = self._get_messages(trace, instructions)

        try:
            response = self.client.chat.completions.create(
                model=self.config.llm.model,
                messages=messages,
                temperature=self.config.llm.temperature,
                top_p=self.config.llm.top_p,
                presence_penalty=self.config.llm.presence_penalty,
                stop=self.config.llm.stop_sequence,
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error("Error generating completion: %s", str(e))
            raise

    async def generate_completion_stream(
        self, trace: Trace, instructions: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming completion using the OpenAI API."""
        messages = self._get_messages(trace, instructions)

        try:
            stream = await self.async_client.chat.completions.create(
                model=self.config.llm.model,
                messages=messages,
                temperature=self.config.llm.temperature,
                top_p=self.config.llm.top_p,
                presence_penalty=self.config.llm.presence_penalty,
                stop=self.config.llm.get_effective_stop_sequence(len(trace.turns) > 0),
                stream=True,
            )

            # Process the stream
            collected_content = ""
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    collected_content += content
                    yield content

        except Exception as e:
            logging.error("Error generating streaming completion: %s", str(e))
            raise
