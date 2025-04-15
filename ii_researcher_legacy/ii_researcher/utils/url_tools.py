"""
URL handling utilities for the II Deep Search
"""

import re
from typing import Any, Dict, List
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlparse, urlunparse


def normalize_url(url_string: str, debug: bool = False) -> str:
    """
    Normalize a URL by standardizing format, removing default ports,
    sorting query parameters, and handling encoding.

    Args:
        url_string: The URL to normalize
        debug: Whether to print debug information

    Returns:
        Normalized URL string

    Raises:
        ValueError: If the URL is empty or invalid
    """
    if not url_string or not url_string.strip():
        raise ValueError("Empty URL")

    url_string = url_string.strip()

    # Add protocol if missing
    if not re.match(r"^[a-zA-Z][a-zA-Z\d+\-.]*:", url_string):
        url_string = "https://" + url_string

    try:
        # Parse the URL
        parsed = urlparse(url_string)

        # Normalize hostname
        netloc = parsed.netloc.lower()
        hostname, port = netloc.split(":", 1) if ":" in netloc else (netloc, None)

        if hostname.startswith("www."):
            hostname = hostname[4:]

        # Handle port
        if port is not None:
            if (parsed.scheme == "http" and port == "80") or (parsed.scheme == "https" and port == "443"):
                netloc = hostname
            else:
                netloc = f"{hostname}:{port}"
        else:
            netloc = hostname

        # Normalize path
        path_segments = []
        for segment in parsed.path.split("/"):
            if not segment:
                continue
            try:
                path_segments.append(unquote(segment))
            except Exception as e:
                if debug:
                    print(f"Failed to decode path segment: {segment}", e)
                path_segments.append(segment)

        normalized_path = "/" + "/".join(path_segments)
        if parsed.path.endswith("/") and normalized_path != "/":
            normalized_path += "/"

        # Replace multiple slashes with single slash
        normalized_path = re.sub(r"/+", "/", normalized_path)

        # Sort query parameters
        query_items = []
        for key, value in sorted(parse_qsl(parsed.query), key=lambda x: x[0]):
            if not key:
                continue

            if value == "":
                query_items.append((key, ""))
                continue

            try:
                decoded_value = unquote(value)
                if quote(decoded_value) == value:
                    query_items.append((key, decoded_value))
                else:
                    query_items.append((key, value))
            except Exception as e:
                if debug:
                    print(f"Failed to decode query param {key}={value}", e)
                query_items.append((key, value))

        query = urlencode(query_items)

        # Handle fragment
        fragment = parsed.fragment
        if fragment in ["", "top", "/"]:
            fragment = ""
        elif fragment:
            try:
                decoded_fragment = unquote(fragment)
                if quote(decoded_fragment) == fragment:
                    fragment = decoded_fragment
            except Exception as e:
                if debug:
                    print(f"Failed to decode fragment: {fragment}", e)

        # Reconstruct the URL
        normalized_url = urlunparse((parsed.scheme, netloc, normalized_path, parsed.params, query, fragment))

        # Final URL validation
        try:
            decoded_url = unquote(normalized_url)
            if quote(decoded_url) == normalized_url:
                normalized_url = decoded_url
        except Exception as e:
            if debug:
                print("Failed to decode final URL", e)

        return normalized_url

    except Exception as error:
        raise ValueError(f'Invalid URL "{url_string}": {error}') from error


def get_unvisited_urls(all_urls: Dict[str, Any], visited_urls: List[str]) -> List[Any]:
    """
    Filter a dictionary of URLs to return only those that haven't been visited.

    Args:
        all_urls: Dictionary mapping URLs to search result objects
        visited_urls: List of already visited URLs

    Returns:
        List of search result objects for unvisited URLs
    """
    return [result for url, result in all_urls.items() if url not in visited_urls]


def extract_domain(url: str) -> str:
    """
    Extract the domain from a URL

    Args:
        url: The URL to extract the domain from

    Returns:
        The domain
    """
    parsed = urlparse(url)
    return parsed.netloc
