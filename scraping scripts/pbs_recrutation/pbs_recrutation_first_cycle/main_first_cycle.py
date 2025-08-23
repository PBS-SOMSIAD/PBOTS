import asyncio
import json
import re
from datetime import datetime
from urllib.parse import urljoin

from crawl4ai import AsyncWebCrawler


def parse_studies_final(markdown_content, base_url):
    programs = []
    is_parsing_table = False

    for line in markdown_content.strip().split('\n'):
        stripped_line = line.strip()

        if is_parsing_table:
            if not stripped_line or '|' not in stripped_line:
                break

            columns = [col.strip() for col in stripped_line.split('|')]

            if len(columns) == 5:
                name_raw = columns[0]
                study_type = columns[1]
                study_mode = columns[2]
                duration = columns[3]
                link_raw = columns[4]

                name_match = re.search(r'\[\s*\*\*(.*?)\*\*\s*]', name_raw)
                name = name_match.group(1).strip() if name_match else None

                link_match = re.search(r'\((.*?)\)', link_raw)
                link = urljoin(base_url, link_match.group(1)) if link_match else None

                if name and link:
                    program = {
                        'name': name,
                        'type': study_type,
                        'mode': study_mode,
                        'duration': duration,
                        'link': link
                    }
                    programs.append(program)

        if '---|---|---|' in stripped_line:
            is_parsing_table = True

    return {'programs': programs}


async def scrape_studies():
    base_url = "https://pbs.edu.pl/pl/oferta-dydaktyczna/studia-i-stopnia"
    async with AsyncWebCrawler(verbose=True) as crawler:
        print(f"Fetching: {base_url}")
        try:
            result = await crawler.arun(url=base_url, bypass_cache=True)
            if result.success:
                parsed_data = parse_studies_final(result.markdown, base_url)

                # Add metadata
                parsed_data["source"] = base_url
                parsed_data["scraped_at"] = datetime.now().isoformat()

                # Save to file
                with open("pbs_studies_first_cycle.json", "w", encoding="utf-8") as f:
                    json.dump(parsed_data, f, ensure_ascii=False, indent=2)

                if parsed_data.get('programs'):
                    print(f"SUCCESS! Saved {len(parsed_data['programs'])} programs to pbs_studies_first_cycle.json")
                else:
                    print("\nSomething went wrong. No programs found.")

            else:
                print(f"Fetch error: {result.error_message}")

        except Exception as e:
            print(f"Critical error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_studies())
