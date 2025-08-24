# embed_and_save_news.py
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Model do embeddingów
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Ścieżka do pliku z aktualnościami
json_file = Path("aktualności.json")

def build_text(item: dict) -> str:
    """Zbuduj tekst do embeddingu na podstawie announcement + content."""
    parts = []
    if item.get("announcement"):
        parts.append(item["announcement"])
    if item.get("content"):
        parts.append(item["content"])
    return " ".join(parts)

# Wczytaj plik
with open(json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Iteracja po sekcjach i ich elementach
for section in data.get("sections", []):
    for item in section.get("items", []):
        text = build_text(item)
        embedding = model.encode(text, convert_to_numpy=True).tolist()
        item["embedding_text"] = text
        item["embedding"] = embedding

# Zapisz zaktualizowany plik
with open(json_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Zaktualizowano {json_file} embeddingami")