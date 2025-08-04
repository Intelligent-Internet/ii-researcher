import os

import requests


class JinaScraper:
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
        jina_api_key = os.environ.get("JINA_API_KEY")
        if not jina_api_key:
            print("Error: JINA_API_KEY environment variable not set")
            return None

        jina_url = f"https://r.jina.ai/{self.link}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {jina_api_key}",
            "X-Engine": "browser",
            "X-Return-Format": "markdown",
        }

        try:
            response = requests.get(jina_url, headers=headers)
            if response.status_code == 200:
                json_response = response.json()
                return json_response["data"]["content"], json_response["data"]["title"]
        except Exception as e:
            print(f"Error: {e}. Failed fetching content from URL.")
            return "", ""
