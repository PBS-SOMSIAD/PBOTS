# embed_and_save.py
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
data_dir = Path("/content/1")

def build_text(item: dict) -> str:
    """Convert structured record into a string for embedding."""
    parts = []
    if item.get("academicTitle"):
        parts.append(item["academicTitle"])
    if item.get("firstName") and item.get("lastName"):
        parts.append(f"{item['firstName']} {item['lastName']}")
    if "disciplines" in item and item["disciplines"]:
        parts.append("discipline: " + ", ".join(item["disciplines"]))
    if "additionalData" in item and item["additionalData"]:
        job = item["additionalData"][0].get("job")
        unit = item["additionalData"][0].get("unitName")
        if job:
            parts.append(f"job: {job}")
        if unit:
            parts.append(f"unit: {unit}")
    return ", ".join(parts)

for json_file in data_dir.glob("*.json"):
    with open(json_file, "r") as f:
        data = json.load(f)

    texts = [build_text(item) for item in data]
    embeddings = model.encode(texts, convert_to_numpy=True).tolist()

    for item, emb in zip(data, embeddings):
        item["embedding"] = emb
        item["embedding_text"] = build_text(item)  # keep for reference

    with open(json_file, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Updated {json_file} with embeddings")