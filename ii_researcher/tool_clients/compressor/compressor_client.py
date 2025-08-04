import os
import json
import openai
from typing import TypedDict
import logging


class Passage(TypedDict):
    text: str
    query: str


async def extract_relevant_segments(passage: Passage) -> str:
    """
    Extract relevant segment numbers from a passage based on a query.

    Args:
        passage: A dictionary containing 'text' and 'query' fields

    Returns:
        A dictionary with a 'segment_list' field containing comma-separated segment numbers or ranges
    """
    # Create client with built-in retry logic
    client = openai.AsyncOpenAI(
        base_url=os.environ.get("OPENAI_BASE_URL"),
        api_key=os.environ.get("OPENAI_API_KEY"),
        max_retries=2,  # Configure retry attempts
        timeout=30.0,  # Request timeout in seconds
    )

    prompt = f"""You are an AI assistant specialized in analyzing text passages and extracting relevant segment numbers based on queries.
    Given a PASSAGE containing segments numbered as <#1#>, <#2#>, <#3#>, etc., and a QUERY,
    your task is to extract ONLY the segment numbers from the PASSAGE that are RELEVANT to the QUERY or USEFUL for the process of compressing the text.
    Guidelines:
    1. Analyze each segment carefully for relevance to the query
    2. Include only segments that directly answer or relate to the query, or are USEFUL for the process of compressing the text
    3. Present the segments in a comma-separated format, using ranges when appropriate
    4. Use hyphens to indicate ranges (e.g. "1-3" for segments 1, 2, and 3)
    5. Sort the segments by decreasing relevance
    6. If no segments are relevant, return an empty string
    7. If the passage contains code, return the full code section to the end of the code block
    8. Note that redundant are preferred over wrong ignoring

    PASSAGE:
    {passage['text']}
    
    QUERY:
    {passage['query']}
    
    Respond with just a comma-separated list of segment numbers or ranges (e.g. "1,3,5-7").
        {{
        "segment_list": "1,3,5-7"
    }}
    """

    response = await client.chat.completions.create(
        model=os.environ.get("FAST_LLM"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    try:
        segment_list = json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError as e:
        logging.error(f"LLM Compressor Error: {e}")
        return ""

    print("Returning segment list: ", segment_list["segment_list"])

    return segment_list["segment_list"]
