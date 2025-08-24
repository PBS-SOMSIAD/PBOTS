import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Model do embeddingów
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Ścieżka do pliku
json_file = Path("pbs_studia_jednolite-magisterskie.json")

def build_text(item: dict) -> str:
    """Zbuduj tekst do embeddingu na podstawie pól kierunku studiów."""
    parts = []
    if item.get("nazwa"):
        parts.append(item["nazwa"])
    if item.get("rodzaj_studiow"):
        parts.append(item["rodzaj_studiow"])
    if item.get("system_studiow"):
        parts.append(item["system_studiow"])
    if item.get("czas_trwania"):
        parts.append(item["czas_trwania"])
    if item.get("link"):
        parts.append(item["link"])
    return " | ".join(parts)

# Wczytaj plik
with open(json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Iteracja po kierunkach studiów
for kierunek in data.get("kierunki", []):
    text = build_text(kierunek)
    embedding = model.encode(text, convert_to_numpy=True).tolist()
    kierunek["embedding_text"] = text
    kierunek["embedding"] = embedding

# Zapisz zaktualizowany plik
with open(json_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Zaktualizowano {json_file} embeddingami")