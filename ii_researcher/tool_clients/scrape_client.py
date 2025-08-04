from colorama import Fore, Style

from ii_researcher.config import (
    COMPRESS_EMBEDDING_MODEL,
    COMPRESS_MAX_INPUT_WORDS,
    COMPRESS_MAX_OUTPUT_WORDS,
    COMPRESS_SIMILARITY_THRESHOLD,
    SCRAPER_PROVIDER,
    USE_LLM_COMPRESSOR,
)
from ii_researcher.tool_clients.compressor import (
    ContextCompressor,
    EmbeddingCompressor,
    LLMCompressor,
)

from .scraper import Scraper


class ScrapeClient:
    def __init__(self, query, cfg=None, context_compressor=None):
        """
        Initialize the ScrapeClient
        Args:
            query: str
            cfg: Config (optional)
        """
        self.query = query
        self.cfg = cfg
        if context_compressor:
            self.context_compressor = context_compressor
        else:
            if (
                COMPRESS_EMBEDDING_MODEL is not None
                and len(COMPRESS_EMBEDDING_MODEL.strip()) > 0
            ):
                # Initialize the embedding compressor with the specified similarity threshold
                # and embedding model
                embedding_compressor = EmbeddingCompressor(
                    similarity_threshold=COMPRESS_SIMILARITY_THRESHOLD,
                    embedding_model=COMPRESS_EMBEDDING_MODEL,
                )
                compressors = [embedding_compressor]
            else:
                compressors = []

            if USE_LLM_COMPRESSOR:
                llm_compressor = LLMCompressor()
                compressors.append(llm_compressor)

            self.context_compressor = ContextCompressor(
                compressors=compressors,
                max_input_words=COMPRESS_MAX_INPUT_WORDS,
                max_output_words=COMPRESS_MAX_OUTPUT_WORDS,
            )

            if len(compressors) == 0:
                raise ValueError(
                    "No compressors available. Please check your configuration."
                )

    def _scrape_urls(self, urls):
        """
        Scrapes the urls using browser

        Returns:
            Dict[str, Any]: Scraped content contains the raw content, title, url, image_urls
        """
        scraped_data = []
        user_agent = (
            self.cfg.user_agent
            if self.cfg
            else "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )

        try:
            scraper = Scraper(urls, user_agent, SCRAPER_PROVIDER)
            scraped_data = scraper.run()

        except Exception as e:
            print(f"{Fore.RED}Error in scrape_urls_by_browser: {e}{Style.RESET_ALL}")

        return scraped_data

    def _handle_github_link(self, url):
        """
        Handle github links by converting them to raw links
        """
        if "github.com" in url and "/blob/" in url:
            url = url.replace("github.com", "raw.githubusercontent.com").replace(
                "/blob/", "/"
            )
            return url
        return url

    async def scrape(self, url):
        url = self._handle_github_link(url)
        try:
            scraped_data = self._scrape_urls([url])[0]
            compressed_content = await self.context_compressor.acompress(
                scraped_data["raw_content"],
                title=scraped_data.get("title", self.query),
                query=self.query,
            )
            scraped_data["content"] = compressed_content

            return scraped_data
        except Exception as e:
            print(f"{Fore.RED}Error in scrape_llm: {e}{Style.RESET_ALL}")
            return {
                "raw_content": "",
                "url": url,
                "content": f"Unable to access the content at {url}. Please consider exploring alternative sources to find the information you need.",
            }
