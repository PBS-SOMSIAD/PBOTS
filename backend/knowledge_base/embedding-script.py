import os
import json
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Ścieżki do folderów z danymi
SCRAPING_DIR = "../../scraping scripts" # !!to do: clean the paths, clean the files and folders!!
FAQ_PATH = os.path.join(SCRAPING_DIR, "Scraping Usos", "faq_usos.json")
NEWS_DIR = os.path.join(SCRAPING_DIR, "pbs_aktualnosci", "extracted_news")
EMPLOYEES_PATH = os.path.join(SCRAPING_DIR, "unispace", "unispace_data", "employees.json")
RECRUITMENT_PATH = os.path.join(SCRAPING_DIR, "pbs_recrutation", "pbs_recrutation_faq", "faq.json")

# Konfiguracja Qdrant
QDRANT_URL = "http://localhost:6333"
COLLECTIONS = {
    "faq",
    "news_feed",
    "employees",
    "recruitment"
}

# Model embeddingowy
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

client = QdrantClient(url=QDRANT_URL)
model = SentenceTransformer(EMBEDDING_MODEL)

def get_embedding(text: str):
    return model.encode(text).tolist()

def insert_embeddings(collection, items, text_fields):
    for item in items:
        text = " ".join(str(item.get(field, "")) for field in text_fields)
        embedding = get_embedding(text)
        client.upsert(
            collection_name=collection,
            points=[{
                "id": item.get("id", None) or None,
                "vector": embedding,
                "payload": item
            }]
        )

def process_faq(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    insert_embeddings(COLLECTIONS["faq"], data, ["question", "answer"])

def process_news_feed(news_dir):
    for fname in os.listdir(news_dir):
        if fname.endswith(".json"):
            with open(os.path.join(news_dir, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
            insert_embeddings(
                COLLECTIONS["news_feed"],
                [data],
                ["title", "content", "date"]
            )

def process_employees(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Zbierz wszystkie możliwe dni tygodnia z konsultacji
    days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    text_fields = [
        "firstName",
        "lastName",
        "aliasUTP",
        "uid",
        "academicTitle",
        "disciplines",
        "academicTeacher",
        # additionalData fields
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
    # Rozwijanie zagnieżdżonych pól
    for item in data:
        if "additionalData" in item:
            for k, v in item["additionalData"].items():
                item[f"additionalData.{k}"] = v
            # Rozwijanie konsultacji
            if "consultations" in item["additionalData"]:
                for day in days_of_week:
                    consultations = item["additionalData"]["consultations"].get(day, {})
                    item[f"additionalData.consultations.{day}.from"] = consultations.get("from", "")
                    item[f"additionalData.consultations.{day}.to"] = consultations.get("to", "")
    insert_embeddings(COLLECTIONS["employees"], data, text_fields)

def process_recruitment(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    insert_embeddings(COLLECTIONS["recruitment"], data, ["name", "type", "mode", "duration"])

if __name__ == "__main__":
    process_faq(FAQ_PATH)
    process_news_feed(NEWS_DIR)
    process_employees(EMPLOYEES_PATH)
    process_recruitment(RECRUITMENT_PATH)


# import os
# import json

# COLLECTIONS = {
#     "faq",
#     "news_feed",
#     "employees",
#     "recruitment"
# }

# # FAQ_COLLECTION = "faq"
# # NEWSFEED_COLLECTION = "news_feed"
# # EMPLOYEES_COLLECTION = "employees"
# # RECRUITMENT_COLLECTION = "recruitment"


# def insert_embeddings(collection, data, text_fields):
#     for item in data:
#         text = " ".join(str(item[field]) for field in text_fields if field in item)
#         # Here you would typically call your embedding model
#         embedding = get_embedding(text)
#         # Then insert the embedding into your database
#         database.insert(collection, {"embedding": embedding, **item})


# def process_faq(json_path):
#     # FAQ: [{"question": "...", "answer": "..."}] 
#     with open(json_path, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     insert_embeddings(COLLECTIONS["faq"], data, text_fields=["question", "answer"]) # category

# def process_recruitment(json_path):
#     # Recruitment: [{"name": "...", "type": "...", "mode": "...", "duration": "...", "link": "..."}]
#     with open(json_path, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     insert_embeddings(
#         COLLECTIONS["recruitment"],
#         data,
#         text_fields=["name", "type", "mode", "duration"]
#     )

# def process_news_feed(json_path):
#     # News Feed: [{"url": "...", "date": "...", "title": "...", "content": "..."}]
#     with open(json_path, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     insert_embeddings(
#         COLLECTIONS["news_feed"],
#         data,
#         text_fields=["url", "date", "title", "content"]
#     )

# def process_employees(json_path):
#     with open(json_path, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     # Include all relevant fields for embedding, including nested fields
#     text_fields = [
#         "firstName",
#         "lastName",
#         "aliasUTP",
#         "uid",
#         "academicTitle",
#         "disciplines",
#         "academicTeacher",
#         # additionalData fields
#         "additionalData.unitName",
#         "additionalData.functions",
#         "additionalData.campus",
#         "additionalData.roomSpaceManagerId",
#         "additionalData.subUnitName",
#         "additionalData.consultations.wednesday.from",
#         "additionalData.consultations.wednesday.to",
#         "additionalData.building",
#         "additionalData.room",
#         "additionalData.subUnitCode",
#         "additionalData.phoneNumber",
#         "additionalData.occupationalGroup",
#         "additionalData.ewidNo",
#         "additionalData.floor",
#         "additionalData.job"
#     ]
#     insert_embeddings(
#         COLLECTIONS["employees"],
#         data,
#         text_fields=text_fields
#     )

# def process_announcements(json_path):
#     with open(json_path, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     # The correct text fields based on your data are "announcement" and "content"
#     insert_embeddings(COLLECTIONS["announcements"], data, text_fields=["announcement", "content"])

# if __name__ == "__main__":
#     process_employees("data/employees.json")
#     process_faq("data/faq.json")
#     process_recruitment("data/recruitment.json")
#     process_news_feed("data/pbs_news_feed.json")
