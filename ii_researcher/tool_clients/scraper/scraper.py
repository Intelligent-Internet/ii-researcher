import importlib
import logging
import re
import subprocess
import sys
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial

import requests
from bs4 import BeautifulSoup
from cleantext import clean
from colorama import Fore, init
from markdown import markdown

from .beautiful_soup.beautiful_soup import BeautifulSoupScraper
from .browser.browser import BrowserScraper
from .firecrawl.firecrawl import FirecrawlScraper
from .pymupdf.pymupdf import PyMuPDFScraper
from .tavily_extract.tavily_extract import TavilyExtract
from .utils import is_pdf_url
from .youtube.youtube import YoutubeScraper


def markdown_to_text(markdown_string):
    """Converts a markdown string to plaintext"""

    # md -> html -> text since BeautifulSoup can extract text cleanly
    html = markdown(markdown_string)

    # extract text
    soup = BeautifulSoup(html, "html.parser")
    text = "".join(soup.find_all(string=True))

    return text


class Scraper:
    """
    Scraper class to extract the content from the links
    """

    def __init__(self, urls, user_agent, scraper):
        """
        Initialize the Scraper class.
        Args:
            urls:
        """
        self.urls = urls
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.scraper = scraper
        if self.scraper == "tavily_extract":
            self._check_pkg(self.scraper)
        self.logger = logging.getLogger(__name__)

    def run(self):
        """
        Extracts the content from the links
        """
        partial_extract = partial(self.extract_data_from_url, session=self.session)
        with ThreadPoolExecutor(max_workers=20) as executor:
            contents = executor.map(partial_extract, self.urls)
        res = [content for content in contents if content["raw_content"] is not None]
        return res

    def _check_pkg(self, scrapper_name: str) -> None:
        """
        Checks and ensures required Python packages are available for scrapers that need
        dependencies beyond requirements.txt. When adding a new scraper to the repo, update `pkg_map`
        with its required information and call check_pkg() during initialization.
        """
        pkg_map = {
            "tavily_extract": {
                "package_installation_name": "tavily-python",
                "import_name": "tavily",
            },
        }
        pkg = pkg_map[scrapper_name]
        if not importlib.util.find_spec(pkg["import_name"]):
            pkg_inst_name = pkg["package_installation_name"]
            init(autoreset=True)
            print(Fore.YELLOW + f"{pkg_inst_name} not found. Attempting to install...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_inst_name])
                print(Fore.GREEN + f"{pkg_inst_name} installed successfully.")
            except subprocess.CalledProcessError:
                raise ImportError(Fore.RED + f"Unable to install {pkg_inst_name}. Please install manually with "
                                  f"`pip install -U {pkg_inst_name}`")

    def extract_data_from_url(self, link, session):
        """
        Extracts the data from the link with logging
        """
        try:
            # workaround for arxiv links
            if "arxiv.org/abs" in link:
                link = "https://arxiv.org/html/" + link.split("/")[-1]

            Scraper = self.get_scraper(link)
            scraper = Scraper(link, session)

            # Get scraper name
            scraper_name = scraper.__class__.__name__
            self.logger.info("\n=== Using %s ===", scraper_name)

            # Get content
            content, title = scraper.scrape()

            if len(content) < 100:
                self.logger.warning("Content too short or empty for %s", link)
                return {"url": link, "raw_content": None, "title": title}

            # Log results
            self.logger.info("\nTitle: %s", title)
            self.logger.info("Content length: %d characters", len(content) if content else 0)
            self.logger.info("URL: %s", link)
            self.logger.info("=" * 50)

            if not content or len(content) < 100:
                self.logger.warning("Content too short or empty for %s", link)
                return {"url": link, "raw_content": None, "title": title}

            content = markdown_to_text(content)

            content = clean(
                content,
                fix_unicode=True,
                no_urls=True,
                no_line_breaks=True,
                replace_with_url="<URL>",
                lower=False,
            )

            content = content.replace("<br>", "")

            return {"url": link, "raw_content": content, "title": title}

        except Exception as e:
            self.logger.error("Error processing %s: %s", link, str(e))
            return {"url": link, "raw_content": None, "title": ""}

    def get_scraper(self, link):
        """
        The function `get_scraper` determines the appropriate scraper class based on the provided link
        or a default scraper if none matches.

        Args:
          link: The `get_scraper` method takes a `link` parameter which is a URL link to a webpage or a
        PDF file. Based on the type of content the link points to, the method determines the appropriate
        scraper class to use for extracting data from that content.

        Returns:
          The `get_scraper` method returns the scraper class based on the provided link. The method
        checks the link to determine the appropriate scraper class to use based on predefined mappings
        in the `SCRAPER_CLASSES` dictionary. If the link ends with ".pdf", it selects the
        `PyMuPDFScraper` class.
        """

        SCRAPER_CLASSES = {
            "pdf": PyMuPDFScraper,
            "bs": BeautifulSoupScraper,
            "browser": BrowserScraper,
            "tavily_extract": TavilyExtract,
            "youtube": YoutubeScraper,
            "firecrawl": FirecrawlScraper,
        }

        scraper_key = None

        youtube_regex = re.compile(
            r"^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|shorts\/)|youtu\.be\/)[\w-]+",
            re.IGNORECASE,
        )

        if link.endswith(".pdf"):
            scraper_key = "pdf"
        elif is_pdf_url(link):
            scraper_key = "pdf"
        elif bool(youtube_regex.match(link)):
            scraper_key = "youtube"
        else:
            scraper_key = self.scraper
        scraper_class = SCRAPER_CLASSES.get(scraper_key)
        if scraper_class is None:
            raise Exception("Scraper not found.")

        return scraper_class
