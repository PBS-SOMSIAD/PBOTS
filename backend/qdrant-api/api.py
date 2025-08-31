import uvicorn
import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from qdrant_client import QdrantClient

class DatabaseGenerationResponse(BaseModel):
    status: str
    document_count: int

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "baza"
LOCAL_JSON_FOLDER = "./data"  # folder where your JSON/txt files are stored

app = FastAPI(
    title="Baza danych o PBS",
    description="API do odpowiadania na temat pytań o PBŚ",
    version="1.0.0",
)

@app.post("/generate_database")
async def generate_database() -> DatabaseGenerationResponse:
    try:
        db_client = QdrantClient(location=QDRANT_URL)
        db_client.set_model(EMBEDDING_MODEL)
        db_client.set_sparse_model("Qdrant/bm25")

        documents, metadatas = [], []

        # Recursively iterate over all JSON and TXT files
        for root, dirs, files in os.walk(LOCAL_JSON_FOLDER):
            for filename in files:
                path = os.path.join(root, filename)

                # JSON files
                if filename.endswith(".json"):
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    items = data if isinstance(data, list) else [data]

                    for item in items:
                        text = json.dumps(item, ensure_ascii=False)
                        metadata = {
                            "source_file": path,
                            "original_type": type(item).__name__
                        }

                        if not text.strip():
                            continue

                        documents.append(text)
                        metadatas.append(metadata)

                # TXT files
                elif filename.endswith(".txt"):
                    with open(path, "r", encoding="utf-8") as f:
                        text = f.read()

                    if not text.strip():
                        continue

                    metadata = {
                        "source_file": path,
                        "original_type": "txt"
                    }

                    documents.append(text)
                    metadatas.append(metadata)

        if not documents:
            raise HTTPException(status_code=400, detail="No valid documents found.")

        # Add all documents to Qdrant
        db_client.add(
            collection_name=COLLECTION_NAME,
            documents=documents,
            metadata=metadatas,
            batch_size=64,
        )

        return DatabaseGenerationResponse(
            status="success", document_count=len(documents)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate database: {str(e)}"
        )

@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)
