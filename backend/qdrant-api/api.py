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
async def generate_database(
    user_context: UserContext = Depends(get_user_context),
) -> DatabaseGenerationResponse:

    # Check if user has admin role
    if not user_context.has_role("admin"):
        raise HTTPException(
            status_code=403,
            detail="Access denied. Admin role required to generate database.",
        )

    try:
        doc_converter = DocumentConverter(allowed_formats=[InputFormat.PDF])
        db_client = QdrantClient(location=QDRANT_URL)
        db_client.set_model(EMBEDDING_MODEL)
        db_client.set_sparse_model(SPARSE_MODEL)

        result = doc_converter.convert("knowledge.pdf")

        documents, metadatas = [], []
        for chunk in HybridChunker().chunk(result.document):
            documents.append(chunk.text)
            metadatas.append(chunk.meta.export_json_dict())

        db_client.add(
            collection_name=COLLECTION_NAME,
            documents=documents,
            metadata=metadatas,
            batch_size=BATCH_SIZE,
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
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
