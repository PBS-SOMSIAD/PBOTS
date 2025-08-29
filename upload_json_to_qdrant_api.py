import os
import requests
import glob

def upload_json_to_qdrant_api(json_path, doc_type="unknown"):
    url = "http://localhost:8001/upload_json"
    with open(json_path, "rb") as f:
        files = {"file": (os.path.basename(json_path), f, "application/json")}
        data = {"doc_type": doc_type}
        response = requests.post(url, files=files, data=data)
        print(f"{json_path}: {response.status_code} {response.text}")

if __name__ == "__main__":
    # Przeszukaj wszystkie pliki json w data/ i podfolderach
    for coll in ["faq", "aktualnosci", "rekrutacja", "pracownicy"]:
        for json_path in glob.glob(f"data/{coll}/**/*.json", recursive=True):
            upload_json_to_qdrant_api(json_path, doc_type=coll)
    print("\n🎉 Wszystkie pliki JSON uploadowane do Qdrant przez API!")
