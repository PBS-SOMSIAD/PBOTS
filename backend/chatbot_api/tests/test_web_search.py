from chatbot_api.web_search import WebSearchTool, SearchList, SearchResult

def test_web_search():
    tool = WebSearchTool()
    results = tool.web_search("wikipedia", max_results=1)
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