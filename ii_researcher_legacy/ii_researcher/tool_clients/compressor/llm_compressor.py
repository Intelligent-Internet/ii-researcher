from typing import List

from baml_client.async_client import b
from baml_client.types import Passage

from .base import Compressor


class LLMCompressor(Compressor):

    async def acompress(self, chunks: List[str], title: str, query: str) -> List[int]:
        numbered_chunks = " ".join([f"<#{i+1}#> {chunk}" for i, chunk in enumerate(chunks)
                                   ])  # +1 because numbered_chunks is 1-indexed
        related = (await b.ExtractRelevantSegments(
            passage=Passage(text=numbered_chunks, query=query),
        )).segment_list

        return [num - 1 for num in parse_segment_numbers(related) if num >= 1
               ]  # -1 because numbered_chunks is 1-indexed


def parse_segment_numbers(segment_list: str) -> List[int]:
    """
    Parse a string of segment numbers in format like "4-6,8-9" into a list of integers.

    Args:
        segment_list (str): String containing segment numbers and ranges, sorted by decreasing relevance

    Returns:
        List[int]: List of segment numbers, sorted by decreasing relevance
    """
    if segment_list.strip() == "":
        return []

    seen = set()
    result = []

    # Split by comma to handle multiple ranges
    for part in segment_list.split(","):
        if "-" in part:
            # Handle range (e.g., "4-6")
            start, end = map(int, part.split("-"))
            for num in range(start, end + 1):
                if num not in seen:
                    seen.add(num)
                    result.append(num)
        else:
            # Handle single number
            num = int(part)
            if num not in seen:
                seen.add(num)
                result.append(num)

    return result  # Already in order of relevance
