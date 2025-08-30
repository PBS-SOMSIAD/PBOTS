import uvicorn
import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from qdrant_client import QdrantClient
from docling.chunking import HybridChunker

class DatabaseGenerationResponse(BaseModel):
    status: str
    document_count: int

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "handbook"
LOCAL_JSON_FOLDER = "./data"  # folder where your JSON files are stored

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

        # Recursively iterate over all JSON files in folder and subfolders
        for root, dirs, files in os.walk(LOCAL_JSON_FOLDER):
            for filename in files:
                if filename.endswith(".json"):
                    path = os.path.join(root, filename)
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    text = data.get("text")
                    metadata = data.get("metadata", {})

                    if not text:
                        continue

                    # Chunk the text
                    for chunk in HybridChunker().chunk(text):
                        documents.append(chunk.text)
                        metadatas.append({**metadata, **chunk.meta.export_json_dict()})

        if not documents:
            raise HTTPException(status_code=400, detail="No valid documents found.")

        # Add to Qdrant
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
