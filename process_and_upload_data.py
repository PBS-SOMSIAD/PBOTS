import os
import json
import uuid
from sentence_transformers import SentenceTransformer

# -----------------------------
# CONFIG: Set to True to upload to Qdrant, False to only save embeddings
# -----------------------------
UPLOAD_TO_QDRANT = True  # Change to True for direct upload

# -----------------------------
# 1. Load embedding model
# -----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")  # dim=384

# -----------------------------
# 2. Helper functions
# -----------------------------
def get_all_json_files(root_dir):
    """
    Returns a list of file paths for all JSON files in root_dir (recursively).
    """
    files = []
    for root, dirs, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith(".json"):
                files.append(os.path.join(root, file))
    return files

def load_json_as_text(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}")
        return None

def embed_jsons_in_directory(root_dir, output_dir):
    """
    Embeds all JSON files in root_dir (recursively) and saves them as .emb.json in output_dir/baza/
    """
    files_to_process = get_all_json_files(root_dir)
    out_coll_dir = os.path.join(output_dir, "baza")
    os.makedirs(out_coll_dir, exist_ok=True)
    for file_path in files_to_process:
        text = load_json_as_text(file_path)
        if text:
            vector = model.encode(text).tolist()
            out_path = os.path.join(out_coll_dir, f"{os.path.basename(file_path)}.emb.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump({"vector": vector, "content": text, "path": file_path}, f, ensure_ascii=False, indent=2)

def upload_embedded_to_qdrant(output_dir):
    """
    Uploads all .emb.json files in output_dir/baza/ to Qdrant collection 'baza'.
    """
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as rest

    client = QdrantClient(host="localhost", port=6333)
    coll_dir = os.path.join(output_dir, "baza")
    if not os.path.isdir(coll_dir):
        print("⚠️ No 'baza' directory found in embedded_data!")
        return
    print(f"\n📂 Uploading collection: baza")
    client.recreate_collection(
        collection_name="baza",
        vectors_config=rest.VectorParams(size=384, distance=rest.Distance.COSINE),
    )
    points = []
    for fname in os.listdir(coll_dir):
        if fname.endswith(".emb.json"):
            with open(os.path.join(coll_dir, fname), "r", encoding="utf-8") as f:
                emb = json.load(f)
            points.append(
                rest.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=emb["vector"],
                    payload={"path": emb["path"], "content": emb["content"]}
                )
            )
    if points:
        client.upsert(collection_name="baza", points=points)
        print(f"✅ Uploaded {len(points)} documents to 'baza'")
    else:
        print(f"⚠️ No embeddings found for 'baza'")

if __name__ == "__main__":
    # Embed all JSONs in the specified folders to one collection 'baza'
    output_dir = "embedded_data"
    for coll in ["faq", "aktualnosci", "rekrutacja", "pracownicy"]:
        root_dir = f"data/{coll}"
        print(f"Embedding: {coll}")
        embed_jsons_in_directory(root_dir, output_dir)
    print("\n🎉 Wszystkie dane zembedowane do 'baza'!")

    if UPLOAD_TO_QDRANT:
        upload_embedded_to_qdrant(output_dir)
        print("\n🎉 Wszystkie dane uploadowane do Qdrant (kolekcja 'baza')!")