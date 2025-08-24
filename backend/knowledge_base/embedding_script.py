import os
import json
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from sentence_transformers import SentenceTransformer

# Ścieżki do folderów z danymi
PREPROCESSED_DIR = "C:\\Users\\Karolina\\Documents\\SOMSIAD\\PBOTS\\preprocessed_data"
FAQ_DIR = os.path.join(PREPROCESSED_DIR, "faq")
NEWS_DIR = os.path.join(PREPROCESSED_DIR, "news_feed")
EMPLOYEES_DIR = os.path.join(PREPROCESSED_DIR, "employees")
RECRUITMENT_DIR = os.path.join(PREPROCESSED_DIR, "recruitment")

# Konfiguracja Qdrant
QDRANT_URL = "http://localhost:6333"
COLLECTIONS = {
    "faq": "faq",
    "news_feed": "news_feed",
    "employees": "employees",
    "recruitment": "recruitment"
}

# Model embeddingowy
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

client = QdrantClient(url=QDRANT_URL)
model = SentenceTransformer(EMBEDDING_MODEL)

def get_embedding(text: str):
    return model.encode(text).tolist()

def ensure_collection(collection_name, vector_size=384):
    existing = [col.name for col in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )

def insert_embeddings(collection, items, text_fields):
    ensure_collection(collection)
    for idx, item in enumerate(items):
        # Sprawdź, czy item jest dict
        if not isinstance(item, dict):
            print(f"[ERROR] Pomijam rekord, bo nie jest dict: {item}")
            continue
        text = " ".join(str(item.get(field, "")) for field in text_fields)
        embedding = get_embedding(text)
        # Ustal id: jeśli nie ma, generuj UUID jako string (fix later, int/string)
        point_id = item.get("id")
        if point_id is None:
            point_id = str(uuid.uuid4())
        # Dodaj logowanie typu i przykładowej zawartości
        if idx == 0:
            print(f"[DEBUG] Przykładowy item do wrzucenia jako payload: {type(item)} -> {item}")
        client.upsert(
            collection_name=collection,
            points=[{
                "id": point_id,
                "vector": embedding,
                "payload": item
            }]
        )

def process_json_folder(folder_path, collection, text_fields):
    if not os.path.isdir(folder_path):
        print(f"Katalog nie istnieje: {folder_path}")
        return
    for fname in os.listdir(folder_path):
        fpath = os.path.join(folder_path, fname)
        if os.path.isfile(fpath) and fname.endswith(".json"):
            with open(fpath, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    print(f"Błąd ładowania pliku {fpath}: {e}")
                    continue
                # Jeśli plik zawiera listę, wrzuć całość, jeśli dict - wrzuć jako jeden rekord
                if isinstance(data, list):
                    insert_embeddings(collection, data, text_fields)
                elif isinstance(data, dict):
                    insert_embeddings(collection, [data], text_fields)
                else:
                    print(f"Nieobsługiwany format w pliku: {fpath}")

def process_faq(folder_path):
    process_json_folder(folder_path, COLLECTIONS["faq"], ["question", "answer"])

def process_news_feed(folder_path):
    process_json_folder(folder_path, COLLECTIONS["news_feed"], ["title", "content", "date"])

def process_employees(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Katalog nie istnieje: {folder_path}")
        return
    days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    text_fields = [
        "firstName",
        "lastName",
        "aliasUTP",
        "uid",
        "academicTitle",
        "disciplines",
        "academicTeacher",
        # additionalData
        "additionalData.unitName",
        "additionalData.functions",
        "additionalData.campus",
        "additionalData.roomSpaceManagerId",
        "additionalData.subUnitName",
        "additionalData.building",
        "additionalData.room",
        "additionalData.subUnitCode",
        "additionalData.phoneNumber",
        "additionalData.occupationalGroup",
        "additionalData.ewidNo",
        "additionalData.floor",
        "additionalData.job"
    ]
    for fname in os.listdir(folder_path):
        fpath = os.path.join(folder_path, fname)
        if os.path.isfile(fpath) and fname.endswith(".json"):
            with open(fpath, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    print(f"Błąd ładowania pliku {fpath}: {e}")
                    continue
                # Rozwijanie zagnieżdżonych pól
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = [data]
                else:
                    print(f"Nieobsługiwany format w pliku: {fpath}")
                    continue
                for item in items:
                    if "additionalData" in item:
                        if isinstance(item["additionalData"], dict):
                            for k, v in item["additionalData"].items():
                                item[f"additionalData.{k}"] = v
                            if "consultations" in item["additionalData"]:
                                for day in days_of_week:
                                    consultations = item["additionalData"]["consultations"].get(day, {})
                                    item[f"additionalData.consultations.{day}.from"] = consultations.get("from", "")
                                    item[f"additionalData.consultations.{day}.to"] = consultations.get("to", "")
                        elif isinstance(item["additionalData"], list):
                            for i, elem in enumerate(item["additionalData"]):
                                item[f"additionalData.list_{i}"] = elem
                                if isinstance(elem, dict):
                                    for k, v in elem.items():
                                        item[f"additionalData.list_{i}.{k}"] = v
                        else:
                            print(f"Pomijam additionalData w rekordzie (nie jest dict ani list): {type(item['additionalData'])}")
                insert_embeddings(COLLECTIONS["employees"], items, text_fields)

def process_recruitment(folder_path):
    process_json_folder(folder_path, COLLECTIONS["recruitment"], ["name", "type", "mode", "duration"])

if __name__ == "__main__":
    process_faq(FAQ_DIR)
    process_news_feed(NEWS_DIR)
    process_employees(EMPLOYEES_DIR)
    process_recruitment(RECRUITMENT_DIR)
    print("Embedding insertion completed (hopefully).") # sybau
