import requests
import sys

# Add path variable

try:
    from ..configs import RAG_URL
except ImportError:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from configs import RAG_URL


def call_search(query_data, max_result=8):
    url = f"{RAG_URL}/search"
    response = requests.post(url, json={"query": query_data, "top_k": max_result})
    values = response.json()["results"][:max_result]
    str_format = []
    for index, res in enumerate(values):
        url_paper = res["url"]
        preview = res["preview"]
        title = res.get("title", None)
        if title is not None:
            str_format.append(
                f"""\nIndex: {index}\nURL: {url_paper}\nTitle: {title}\nPreview: {preview}\n"""
            )
        else:
            str_format.append(
                f"""\nIndex: {index}\nURL: {url_paper}\nPreview: {preview}\n"""
            )
    return "".join(str_format)


def web_search(query, max_result=5):
    return call_search(query, max_result)


def call_visit(url):
    endpoint = f"{RAG_URL}/visit"
    response = requests.post(endpoint, json={"url": url})
    data = response.json()
    if "data" not in data:
        print("\n\nPlease use exactly url returned from the web_search!!!")
        raise Exception(
            f"{data}\n\nPlease use exactly url returned from the web_search!!!"
        )
    return response.json()["data"]


def visit_webpage(url):
    return call_visit(url)


if __name__ == "__main__":
    print(web_search("complications of relapsing polychondritis"))
    print(visit_webpage("https://pubmed.gov/article/pubmed23n1166_9461"))
