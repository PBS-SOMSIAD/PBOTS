import uvicorn

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from qdrant_client import QdrantClient
from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter
import os


class DatabaseGenerationResponse(BaseModel):
    status: str
    document_count: int


QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "handbook"


app = FastAPI(
    title="Baza danych o PBS",
    description="API do odpowiadania na temat pytań o PBŚ",
    version="1.0.0",
)


@app.post("/generate_database")
async def generate_database() -> DatabaseGenerationResponse:
    try:
        doc_converter = DocumentConverter(allowed_formats=[InputFormat.PDF])
        db_client = QdrantClient(location=QDRANT_URL)
        db_client.set_model(EMBEDDING_MODEL)
        db_client.set_sparse_model("Qdrant/bm25")

        result = doc_converter.convert(
            "https://media.wizards.com/2014/downloads/dnd/PlayerDnDBasicRules_v0.2_PrintFriendly.pdf"
        )

        documents, metadatas = [], []
        for chunk in HybridChunker().chunk(result.document):
            documents.append(chunk.text)
            metadatas.append(chunk.meta.export_json_dict())

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
