import asyncio
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .base import Compressor


class ContextCompressor:

    def __init__(
        self,
        compressors: List[Compressor],
        max_output_words: int = 4000,
        max_input_words: int = 16000,
        chunk_size: int = 1000,
        chunk_overlap: int = 0,
    ):
        """
        max_output_words: max output words
        max_input_words: max input words
        chunk_size: chunk size
        chunk_overlap: chunk overlap
        """
        self.compressors = compressors
        self.max_output_words = max_output_words
        self.max_input_words = max_input_words
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    async def acompress(self, context, title, query) -> str:
        context = " ".join(context.split()[:self.max_input_words])
        chunks = self.text_splitter.split_text(context)

        words_in_chunks = [len(chunk.split()) for chunk in chunks]

        compressor_results = await asyncio.gather(
            *[compressor.acompress(chunks, title, query) for compressor in self.compressors])

        set_compressor_results = [set(compressor_result) for compressor_result in compressor_results]

        # assert that all compressor results are subsets of the chunks
        all_chunks_set = set(range(len(chunks)))
        for compressor_result in compressor_results:
            assert set(compressor_result).issubset(
                all_chunks_set), f"Compressor result {compressor_result} is not a subset of all chunks {all_chunks_set}"

        intersection = set.intersection(*set_compressor_results)
        union = set.union(*set_compressor_results)

        # get total words in union
        total_words_in_union = sum(words_in_chunks[i] for i in union)
        total_words_in_intersection = sum(words_in_chunks[i] for i in intersection)

        if total_words_in_intersection > self.max_output_words:
            # Since all compressors agree on intersection items, use the first compressor's
            # ordering to determine relevance (already sorted by decreasing relevance)
            sorted_intersection = [i for i in compressor_results[0] if i in intersection]

            # Keep only the most relevant chunks that fit within the word limit
            current_words = 0
            filtered_intersection = []
            for chunk_idx in sorted_intersection:
                if current_words + words_in_chunks[chunk_idx] <= self.max_output_words:
                    filtered_intersection.append(chunk_idx)
                    current_words += words_in_chunks[chunk_idx]
                else:
                    break

            return "\n".join(chunks[i] for i in sorted(filtered_intersection))
        if total_words_in_union > self.max_output_words:
            # First include all intersection chunks
            result_indices = list(intersection)
            current_words = total_words_in_intersection

            # Rank the remaining chunks in union-intersection
            chunk_ranks = {}
            for idx in union - intersection:
                # Calculate a rank based on position across compressors
                # Lower rank means higher relevance
                rank = 0
                for compressor_result in compressor_results:
                    if idx in compressor_result:
                        rank += compressor_result.index(idx)
                    else:
                        # If not present, penalize by adding length of result + 1
                        rank += len(compressor_result) + 1
                # Average position for all compressors
                # Lower rank means higher relevance
                chunk_ranks[idx] = rank / len(compressor_results)

            # Add remaining chunks in order of relevance until we hit the limit
            # Sort by ascending rank (lower rank = higher relevance)
            sorted_remaining = sorted(union - intersection, key=lambda idx: chunk_ranks[idx])
            for chunk_idx in sorted_remaining:
                if current_words + words_in_chunks[chunk_idx] <= self.max_output_words:
                    result_indices.append(chunk_idx)
                    current_words += words_in_chunks[chunk_idx]
                else:
                    break

            return "\n".join(chunks[i] for i in sorted(result_indices))
        else:  # total_words_in_union <= self.max_output_words
            return "\n".join(chunks[i] for i in sorted(union))
