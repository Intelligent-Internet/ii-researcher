from abc import ABC, abstractmethod
from typing import List


class Compressor(ABC):

    @abstractmethod
    async def acompress(self, chunks: List[str], title: str, query: str) -> List[int]:
        """Compress the chunks of text into a list of integers. Sorted by decreasing relevance."""
