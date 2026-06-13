import json
import os

import requests


class CrwScraper:
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
        Scrapes the url using fastCRW (Firecrawl-compatible web scraper; single
        binary; self-host or cloud).

        Returns:
            Dict[str, Any]: Scraped content
        """
        base_url = (
            os.environ.get("CRW_BASE_URL", "https://fastcrw.com/api") + "/v1/scrape"
        )
        api_key = os.environ.get("CRW_API_KEY")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {"url": self.link, "onlyMainContent": False, "formats": ["markdown"]}
        response = requests.request(
            "POST", base_url, headers=headers, data=json.dumps(payload)
        )
        if response.status_code == 200:
            data = response.json().get("data")
            return data.get("markdown", ""), data.get("metadata").get("title")
        else:
            return "", ""
