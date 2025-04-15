import json
import os

import requests


class FirecrawlScraper:

    def __init__(self, link, session=None):
        """
        Initialize the scraper with a link and an optional session.

        Args:
          link (str): The URL
          session (requests.Session, optional): An optional session for making HTTP requests.
        """
        self.link = link
        self.session = session

    def scrape(self) -> str:
        """
        Scrapes the url using FireCrawl

        Returns:
            Dict[str, Any]: Scraped content
        """
        base_url = "https://api.firecrawl.dev/v1/scrape"
        api_key = os.environ.get("FIRECRAWL_API_KEY")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {"url": self.link, "onlyMainContent": False, "formats": ["markdown"]}
        response = requests.request("POST", base_url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json().get("data")
            return data.get("markdown", ""), data.get("metadata").get("title")
        else:
            return "", ""
