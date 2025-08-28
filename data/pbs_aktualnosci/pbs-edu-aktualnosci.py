from crawl4ai import AsyncWebCrawler
import asyncio
import re
import os
import json
from bs4 import BeautifulSoup
from crawl4ai import CrawlerRunConfig

num_pages_to_crawl = input("Ile stron?")
num_pages_to_crawl = int(num_pages_to_crawl)
# WAŻNE: Ten pattern jest do URL-i pojedynczych ARTYKUŁÓW newsowych (np. http://pbs.edu.pl/pl/aktualnosc/tytul)
# Pozostaje on bez zmian, ponieważ był poprawny dla tego celu.
pattern = re.compile(r"^http://pbs\.edu\.pl/pl/aktualnosc/([^/]+)$")

#Folder końcowy
output_dir = "extracted_news"
os.makedirs(output_dir, exist_ok=True)

# Set aby unikac dupliakatów
all_discovered_news_urls = set()

# Extraction function (bez zmian, działa poprawnie dla pojedynczego artykułu)
async def handle_response(response, html: str, url: str):
    print(f"Processing URL in handle_response: {url}")

    match = pattern.match(url)
    if not match:
        print(f"Skipping {url}: URL does not match article pattern.")
        return

    slug = match.group(1)
    soup = BeautifulSoup(html, "html.parser")

    date_div = soup.find("div", class_="news-published-at")
    if not date_div:
        print(f"Skipping {url}: 'news-published-at' div not found.")
        return
    date = date_div.text.strip()

    title_div = soup.find("div", class_="news-title")
    title = title_div.text.strip() if title_div else (soup.title.string.strip() if soup.title else "No Title")
    if title == "No Title":
        print(f"Warning: No title found for {url}")

    # Extract and clean paragraph content
    content_paragraphs = []
    paragraphs = soup.find_all("p")

    for p in paragraphs:
        p_copy = BeautifulSoup(str(p), 'html.parser')
        
        for a_tag in p_copy.find_all("a"):
            a_tag.decompose()

        paragraph_text = p_copy.get_text(strip=True)
        if paragraph_text:
            content_paragraphs.append(paragraph_text)
    
    content = "\n\n".join(content_paragraphs)

    data = {
        "url": url,
        "date": date,
        "title": title,
        "content": content
    }

    filename = f"{date}_{slug}.json"
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved: {filepath}")
    except Exception as e:
        print(f"Error saving file {filepath}: {e}")

# Main runner
async def main():
    async with AsyncWebCrawler() as crawler:
        # Bazowy URL dla stron aktualności (zauważ 'aktualnosci' na końcu)
        base_pagination_url = "https://pbs.edu.pl/pl/aktualnosci" 
        
        # PROSTA PĘTLA: Określ liczbę stron, które chcesz przeszukać.
        # Zmień tę wartość na taką, która odpowiada liczbie stron z aktualnościami.
        # Jeśli jest np. 20 stron, ustaw range(1, 21).
        # Na potrzeby testu zacznij od małej liczby, np. 5.


        run_config = CrawlerRunConfig()
        
        print(f"--- Discovering News Article URLs from {num_pages_to_crawl} Pagination Pages ---")

        # Pętla iterująca po numerach stron od 1 do num_pages_to_crawl
        for current_page in range(1, num_pages_to_crawl + 1):
            # Budujemy pełny URL strony paginacji
            page_url = f"{base_pagination_url}?page={current_page}"
            print(f"Crawling pagination page: {page_url}")

            result = await crawler.arun(url=page_url, config=run_config)

            # Sprawdzamy, czy strona została pomyślnie pobrana
            if not result or not result.html or result.status_code != 200:
                print(f"Failed to fetch {page_url} (Status: {result.status_code if result else 'N/A'}). Skipping this page.")
                continue # Przejdź do następnej iteracji (następnej strony), jeśli ta nie działa

            soup = BeautifulSoup(result.html, "html.parser")
            
            # Wyszukaj linki DO ARTYKUŁÓW na aktualnie pobranej stronie paginacji.
            # Używamy do tego 'pattern', który jest przeznaczony dla URL-i artykułów.
            news_links_on_page = soup.find_all("a", href=pattern)
            
            newly_discovered_on_page = 0
            for link in news_links_on_page:
                href = link.get("href")
                # Dodaj link do zbioru, jeśli pasuje do wzorca artykułu i nie jest duplikatem
                if href and pattern.match(href) and href not in all_discovered_news_urls:
                    all_discovered_news_urls.add(href)
                    newly_discovered_on_page += 1
            
            print(f"Discovered {newly_discovered_on_page} new news URLs on {page_url}. Total unique URLs: {len(all_discovered_news_urls)}")

        print(f"\n--- Finished discovering URLs from all {num_pages_to_crawl} pages. Total unique news articles to process: {len(all_discovered_news_urls)} ---")
        
        if not all_discovered_news_urls:
            print("No news URLs were found across any pagination pages. Please verify the URL pattern and the 'num_pages_to_crawl' setting.")
            return

        print("\n--- Processing Discovered News Articles ---")
        # Teraz przetwórz każdy unikalny link do artykułu
        for article_url in all_discovered_news_urls:
            print(f"Attempting to crawl news article: {article_url}")
            article_result = await crawler.arun(url=article_url, config=run_config)
            
            if article_result:
                print(f"Status code for {article_url}: {article_result.status_code}")
                if article_result.html:
                    await handle_response(article_result, article_result.html, article_result.url)
                else:
                    print(f"No HTML content for {article_url}.")
            else:
                print(f"Failed to fetch news article: {article_url}")

# Execute
if __name__ == "__main__":
    asyncio.run(main())