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
    Returns a list of tuples: (collection_name, file_path)
    Each folder (any depth) will become a separate collection.
    """
    files = []
    for root, dirs, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith(".json"):
                # Make a collection name from relative path
                rel_path = os.path.relpath(root, root_dir)
                collection_name = rel_path.replace(os.sep, "_") or "root"
                files.append((collection_name, os.path.join(root, file)))
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
    Embeds all JSON files in root_dir (recursively) and saves them as .emb.json in output_dir/collection_name/
    """
    files_to_process = get_all_json_files(root_dir)
    collections = {}
    for coll_name, file_path in files_to_process:
        collections.setdefault(coll_name, []).append(file_path)

    for collection_name, files in collections.items():
        out_coll_dir = os.path.join(output_dir, collection_name)
        os.makedirs(out_coll_dir, exist_ok=True)
        for file_path in files:
            text = load_json_as_text(file_path)
            if text:
                vector = model.encode(text).tolist()
                out_path = os.path.join(out_coll_dir, f"{os.path.basename(file_path)}.emb.json")
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump({"vector": vector, "content": text, "path": file_path}, f, ensure_ascii=False, indent=2)

def upload_embedded_to_qdrant(output_dir):
    """
    Uploads all .emb.json files in output_dir/collection_name/ to Qdrant collections.
    """
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as rest

    client = QdrantClient(host="localhost", port=6333)
    for collection_name in os.listdir(output_dir):
        coll_dir = os.path.join(output_dir, collection_name)
        if not os.path.isdir(coll_dir):
            continue
        print(f"\n📂 Uploading collection: {collection_name}")
        client.recreate_collection(
            collection_name=collection_name,
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
            client.upsert(collection_name=collection_name, points=points)
            print(f"✅ Uploaded {len(points)} documents to '{collection_name}'")
        else:
            print(f"⚠️ No embeddings found for '{collection_name}'")

if __name__ == "__main__":
    # Embed all JSONs in the specified folders as collections
    for coll in ["faq", "aktualnosci", "rekrutacja", "pracownicy"]:
        root_dir = f"data/{coll}"
        output_dir = "embedded_data"
        print(f"Embedding collection: {coll}")
        embed_jsons_in_directory(root_dir, output_dir)
    print("\n🎉 All collections embedded!")

    if UPLOAD_TO_QDRANT:
        upload_embedded_to_qdrant(output_dir)
        print("\n🎉 All collections uploaded to Qdrant!")