import asyncio
import json
import re
from datetime import datetime
from crawl4ai import AsyncWebCrawler


def clean_markdown(markdown_content: str) -> str:
    """
    Usuwa wszystko do wzorca 'dni temu  \n---' i zostawia tylko komunikaty
    Potem usuwa stopkę rozpoczynającą się od ![USOS]
    Na końcu czyści zbędne \n przed \n---
    """
    pattern = r"dni temu\s*\n---"
    match = re.search(pattern, markdown_content)

    if match:
        content = markdown_content[match.end():].strip()
    else:
        print("Nie znaleziono wzorca 'dni temu \\n---', zwracam oryginalną treść")
        content = markdown_content

    footer_pattern = r'\n!\[USOS\].*'
    content = re.sub(footer_pattern, '', content, flags=re.DOTALL)

    clean_pattern = r'\n(\s*)\n---'
    content = re.sub(clean_pattern, r'\n---', content)

    return content.strip()


def parse_announcements(cleaned_markdown: str) -> list:
    """
    Parsuje komunikaty według wzorca:
    1. Zapisujemy miejsce startu do zmiennej start
    2. Szukamy drugiego \n--- (czyli muszą być dwa)
    3. Cofamy się do poprzedniego \n
    4. Wszystko od start do tego poprzedniego \n to komunikat
    5. Teraz start jest tam gdzie to \n
    6. Powtarzamy
    """
    announcements = []
    content = cleaned_markdown
    start = 0

    while start < len(content):
        first_separator = content.find('\n---', start)

        if first_separator == -1:
            if start < len(content):
                last_announcement = content[start:].strip()
                if last_announcement:
                    announcements.append(last_announcement)
            break

        second_separator = content.find('\n---', first_separator + 4)

        if second_separator == -1:
            announcement = content[start:].strip()
            if announcement:
                announcements.append(announcement)
            break

        newline_before_second = content.rfind('\n', first_separator + 4, second_separator)

        if newline_before_second == -1:
            announcement = content[start:second_separator].strip()
        else:
            announcement = content[start:newline_before_second].strip()

        if announcement:
            announcements.append(announcement)

        if newline_before_second != -1:
            start = newline_before_second + 1  # +1 żeby pominąć \n
        else:
            start = second_separator

        while start < len(content) and content[start] in ['\n', ' ', '\t']:
            start += 1

    return announcements


def parse_faq(text: str) -> list:
    """
    Parsuje FAQ według algorytmu:
    - Znajdujemy „?", wszystko przed nim to pytanie
    - Szukamy drugiego „?"
    - Cofamy się do poprzedniej kropki „." przed drugim „?"
    - Wszystko od pierwszego „?" (włącznie) do tej kropki (włącznie) to odpowiedź
    - Jeśli nie ma drugiego „?", bierzemy wszystko do końca jako odpowiedź
    """
    faq_items = []
    start = 0

    while start < len(text):

        first_question_mark = text.find('?', start)

        if first_question_mark == -1:
            break

        question = text[start:first_question_mark + 1].strip()

        second_question_mark = text.find('?', first_question_mark + 1)

        if second_question_mark == -1:
            answer = text[first_question_mark + 1:].strip()
            if question and answer:
                faq_items.append({
                    "question": question,
                    "answer": answer
                })
            break
        else:
            last_dot = text.rfind('.', first_question_mark + 1, second_question_mark)

            if last_dot == -1:
                answer = text[first_question_mark + 1:second_question_mark].strip()
                start = second_question_mark
            else:
                answer = text[first_question_mark + 1:last_dot + 1].strip()
                start = last_dot + 1

            if question and answer:
                faq_items.append({
                    "question": question,
                    "answer": answer
                })

    return faq_items


def create_structured_json(announcements: list, source_url: str) -> dict:
    # Specjalne parsowanie dla FAQ - łączymy wszystkie announcements w jeden tekst
    full_text = ' '.join(announcements)
    full_text = re.sub(r'^FAQ - CZĘSTO ZADAWANE PYTANIA\s*\n---\s*\n', '', full_text)
    items = parse_faq(full_text)

    return {
        "source": source_url,
        "scraped_at": datetime.today().strftime('%Y-%m-%d'),
        "sections": [
            {
                "items": items
            }
        ]
    }


async def main():
    url = "https://usosweb.pbs.edu.pl/kontroler.php?_action=news/default&panel=DOMYSLNY&file=6pl.html"
    print(f"Scrapowanie strony FAQ (6pl): {url}")

    async with AsyncWebCrawler() as crawler:
        try:
            result = await crawler.arun(url=url)

            cleaned_markdown = clean_markdown(result.markdown)

            announcements = parse_announcements(cleaned_markdown)

            structured_data = create_structured_json(announcements, url)

            output_file = "structured_announcements_6pl.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(structured_data, f, ensure_ascii=False, indent=2)

            print(f"\nWyniki dla FAQ (6pl):")
            print(f"Znaleziono {len(structured_data['sections'][0]['items'])} pytań FAQ")
            for i, item in enumerate(structured_data['sections'][0]['items'][:3]):
                question = item.get('question', 'Brak pytania')
                print(f"{i + 1}. {question[:60]}...")
            print(f"Zapisano dane do {output_file}\n")

        except Exception as e:
            print(f"Błąd przy scrapowaniu FAQ (6pl): {e}")


if __name__ == "__main__":
    asyncio.run(main())