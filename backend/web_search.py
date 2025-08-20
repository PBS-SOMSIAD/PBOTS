from typing import List, Optional
from pydantic import BaseModel, Field
from ddgs import DDGS
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from urllib.parse import urlparse


class SearchResult(BaseModel):
    url: str = Field(..., description="URL of the search result")
    title: Optional[str] = Field(None, description="Title of the search result")
    snippet: Optional[str] = Field(None, description="Snippet of the search result")
    scraped_content: Optional[str] = Field(
        None, description="Scraped content in markdown"
    )


class SearchList(BaseModel):
    results: List[SearchResult] = Field(
        ..., description="Search results with scraped content"
    )


class WebSearchTool:
    def _validate_url(self, url: str) -> Optional[str]:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None
        return url

    async def search_and_scrape(self, query: str, max_results: int = 1) -> SearchList:
        ddgs = DDGS()
        results = []

        # Get search results
        try:
            search_items = list(ddgs.text(query, max_results=max_results))
        except Exception as e:
            print(f"Search failed: {e}")
            return SearchList(results=[])

        # Setup crawler configs
        browser_conf = BrowserConfig(headless=True)
        run_conf = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

        async with AsyncWebCrawler(config=browser_conf) as crawler:
            for item in search_items:
                url = item.get("href")
                title = item.get("title")
                snippet = item.get("body")

                validated_url = self._validate_url(url)
                if not validated_url:
                    results.append(
                        SearchResult(
                            url=url or "",
                            title=title,
                            snippet=snippet,
                            scraped_content="Invalid URL",
                        )
                    )
                    continue

                try:
                    crawl_result = await crawler.arun(
                        url=validated_url,
                        config=run_conf,
                        check_robots_txt=False,
                        only_text=True,
                        remove_forms=True,
                        remove_overlay_elements=True,
                        exclude_external_links=True,
                        magic=True,
                        simulate_user=True,
                    )
                    if crawl_result.success:
                        scraped_md = crawl_result.markdown.fit_markdown
                    else:
                        scraped_md = f"Crawl failed: {crawl_result.error_message or 'unknown error'}"
                except Exception as e:
                    scraped_md = f"Crawl exception: {e}"

                results.append(
                    SearchResult(
                        url=validated_url,
                        title=title,
                        snippet=snippet,
                        scraped_content=scraped_md,
                    )
                )

        return SearchList(results=results)
