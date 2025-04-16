import asyncio
from typing import List

import numpy as np
from langchain_openai import OpenAIEmbeddings

from ii_researcher.config import OPENAI_BASE_URL

from .base import Compressor


class EmbeddingCompressor(Compressor):

    def __init__(
        self,
        similarity_threshold: float,
        embedding_model: str = "text-embedding-3-large",
    ):
        self._embedding_model = OpenAIEmbeddings(
            model=embedding_model,
            base_url=OPENAI_BASE_URL,
        )
        self.similarity_threshold = similarity_threshold

    def cosine_similarity_batch(self, matrix1, matrix2):
        """
        Compute cosine similarity between two matrices efficiently.
        """
        matrix1 = np.array(matrix1)
        matrix2 = np.array(matrix2)
        norm1 = np.linalg.norm(matrix1, axis=1, keepdims=True)
        norm2 = np.linalg.norm(matrix2, axis=1)
        return np.dot(matrix1, matrix2.T) / (norm1 * norm2)

    async def acompress(self, chunks: List[str], title: str, query: str) -> List[int]:
        query_emb, title_emb, chunks_emb = await asyncio.gather(
            self._embedding_model.aembed_query(query),
            self._embedding_model.aembed_query(title),
            self._embedding_model.aembed_documents(chunks),
        )

        similarities = self.cosine_similarity_batch(chunks_emb, [query_emb, title_emb])

        max_similarities = np.max(similarities, axis=1)
        relevant_indices = np.where(max_similarities >= self.similarity_threshold)[0]
        sorted_indices = relevant_indices[np.argsort(
            -max_similarities[relevant_indices])]  # sort by decreasing of relevance
        return sorted_indices.tolist()
