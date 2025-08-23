import asyncio
import json
from crawl4ai import AsyncWebCrawler
import re

def parse_faq(content):
    sections = {
        "rekrutacja": ["rekrutacja", "matura", "rejestracja", "kierunek"],
        "oplaty": ["opłata", "opłat", "zwrot", "wpłata", "koszt"],
        "dokumenty": ["dokument", "świadectwo", "zdjęcie", "podanie"],
        "wyniki": ["wynik", "klasyfikacja", "przyjęcie", "nieprzyjęcie"],
        "studia": ["studia", "stacjonarne", "niestacjonarne", "progi punktowe"],
        "rodo": ["RODO", "dane osobowe", "ochrona danych", "prywatność"],
        "kontakt": ["kontakt", "email", "telefon", "biuro"],
        "inne": []
    }
    faq_items, current_q, current_a = [], "", ""
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.endswith('?') or (line.isupper() and len(line) < 50):
            if current_q and current_a:
                faq_items.append({
                    "question": current_q.strip(),
                    "answer": current_a.strip(),
                    "category": categorize_question(current_q, sections)
                })
            current_q, current_a = line, ""
        else:
            current_a += " " + line
    if current_q and current_a:
        faq_items.append({
            "question": current_q.strip(),
            "answer": current_a.strip(),
            "category": categorize_question(current_q, sections)
        })
    return {
        "source": "https://pbs.edu.pl/pl/rekrutacja/faq",
        "sections": [
            {"category": cat, "items": [i for i in faq_items if i["category"] == cat]}
            for cat in sections if any(i["category"] == cat for i in faq_items)
        ]
    }

def categorize_question(question, sections):
    q_lower = question.lower()
    for cat, keywords in sections.items():
        if cat != "inne" and any(kw in q_lower for kw in keywords):
            return cat
    return "inne"

async def main():
    try:
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url="https://pbs.edu.pl/pl/rekrutacja/faq",
                bypass_cache=True
            )
            if result.success:
                faq_data = parse_faq(result.markdown)
                with open('pbs_faq.json', 'w', encoding='utf-8') as f:
                    json.dump(faq_data, f, ensure_ascii=False, indent=2)
                print("SUCCESS! Saved 'pbs_faq.json'")
            else:
                print(f"Error: {result.error_message}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())