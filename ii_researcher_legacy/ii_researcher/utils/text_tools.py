import random
import re
from typing import List, TypeVar

T = TypeVar("T")  # Generic type for lists with any element type


def remove_all_line_breaks(text: str) -> str:
    """
    Remove all line breaks from text and replace them with spaces.

    Args:
        text: Input string

    Returns:
        String with line breaks replaced with spaces
    """
    return re.sub(r"(\r\n|\n|\r)", " ", text)


def choose_k(items: List[T], k: int) -> List[T]:
    """
    Randomly sample k items from a list without repetition.

    Args:
        items: List to sample from
        k: Number of items to select

    Returns:
        Random subset of k items (or fewer if input list is smaller than k)
    """
    # Create a copy to avoid modifying the original list
    items_copy = items.copy()

    # Ensure k is not larger than the list length
    k = min(k, len(items_copy))

    # Use random.sample for efficient random sampling without replacement
    return random.sample(items_copy, k)
