from typing import List, Optional
from pydantic import BaseModel, Field
from googlesearch import search
from httpx import Client
from bs4 import BeautifulSoup


class SearchResult(BaseModel):
    url: str = Field(..., description="URL of the search result")

class SearchList(BaseModel):
    results: List[SearchResult] = Field(..., description="Search results")

class WebSearchTool:
    def __init__(
        self,
        language: Optional[str] = "en",
        timeout: Optional[int] = 1,
        sleep_interval: Optional[int] = 1,
    ):
        self.language = language
        self.timeout = timeout
        self.sleep_interval = sleep_interval

    def web_search(
        self,
        query: str,
        max_results: int = 1,
        unique: bool = False,
    ) -> SearchList:
        result_list = []
        results = search(
            term=query,
            num_results=max_results,
            lang=self.language,
            start_num=0,
            unique=unique,
            sleep_interval=self.sleep_interval,
        )
        for _, result in enumerate(results):
            result_list.append(SearchResult(url=result))

        return SearchList(results=result_list)

    def web_scrap(self, url: str) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
         }
        with Client(headers=headers) as client:
            response = client.get(url, timeout=10)
            if response.status_code != 200:
                return f'Failed to fetch {url}. Code: {response.status_code}'

            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.get_text().replace('\n', '').replace('\r', '')

def test_web_search():
    tool = WebSearchTool()
    results = tool.web_search("wikipedia", max_results=1)
    print(results.results[0].url)
    assert isinstance(results, SearchList)
    assert len(results.results) == 1
    assert isinstance(results.results[0], SearchResult)
    assert results.results[0].url.startswith("https://")

def test_web_scrap():
    tool = WebSearchTool()
    url = "https://www.wikipedia.org/"
    content = tool.web_scrap(url)

    assert isinstance(content, str)
    assert "Wikipedia" in content 