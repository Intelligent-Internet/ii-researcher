import json
import http.client
import re
import requests
import numpy as np
from pathlib import Path
import sys

# Import API key
try:
    from ..configs import API_SERP_DEV  # Not used in this script
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent))
    from configs import API_SERP_DEV


def search_serp(query):
    """
    Search query using Serper API and return formatted organic results.
    """
    url = "https://google.serper.dev/search"
    list_key = [API_SERP_DEV]
    np.random.shuffle(list_key)

    for key in list_key:
        try:
            payload = json.dumps({"q": query})
            headers = {"X-API-KEY": key, "Content-Type": "application/json"}

            response = requests.post(url, headers=headers, data=payload)
            res = response.json()

            if "organic" not in res:
                raise Exception(str(res))

            formatted_results = []
            for index, value in enumerate(res["organic"]):
                if "huggingface" in value["link"]:
                    continue
                formatted_results.append(
                    f"\nIndex: {index}\nURL: {value['link']}\nTitle: {value['title']}\nPreview: {value['snippet']}\n"
                )
            return "".join(formatted_results)

        except Exception:
            continue

    raise Exception("All API keys failed")


def remove_links_but_keep_text(text):
    """
    Removes markdown-style links and images but keeps the visible text.
    """
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)  # Image alt text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # Link text
    text = "\n".join([line.strip() for line in text.split("\n") if line.strip()])
    text = " ".join(text.split()[:5000])
    return text


def remove_url_link(text):
    return remove_links_but_keep_text(text)


def visit_serp(url):
    """
    Visit a URL using the Serper scraping API and return cleaned text content.
    """
    list_key = [API_SERP_DEV]
    np.random.shuffle(list_key)

    for key in list_key:
        try:
            conn = http.client.HTTPSConnection("scrape.serper.dev")
            payload = json.dumps({"url": url, "includeMarkdown": False})
            headers = {"X-API-KEY": key, "Content-Type": "application/json"}
            conn.request("POST", "/", payload, headers)
            res = conn.getresponse()
            data = res.read()
            result = json.loads(data.decode("utf-8"))

            if "text" in result:
                return remove_links_but_keep_text(result["text"])
            elif "markdown" in result:
                return remove_links_but_keep_text(result["markdown"])
            else:
                raise Exception(str(result))

        except Exception:
            continue

    raise Exception("All scraping API keys failed")


def web_search(query, max_result=5):
    """
    Performs a web search and returns formatted result.
    """
    return search_serp(query)


def visit_webpage(url):
    """
    Retrieves and processes the text from a given webpage URL.
    """
    return visit_serp(url)


if __name__ == "__main__":
    print(web_search("complications of relapsing polychondritis"))
