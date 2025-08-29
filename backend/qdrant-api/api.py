import uvicorn
import os
import json

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter


class UploadJsonResponse(BaseModel):
    status: str
    uploaded_count: int


class UploadDocumentResponse(BaseModel):
    status: str
    uploaded_count: int


class UploadDirectoryResponse(BaseModel):
    status: str
    collections: dict


QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

app = FastAPI(
    title="PBS Knowledge Base API",
    description="API for answering PBS questions",
    version="1.0.0",
)


def create_collection_if_not_exists(client, collection_name, dim=384):
    if collection_name not in [c.name for c in client.get_collections().collections]:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=rest.VectorParams(size=dim, distance=rest.Distance.COSINE),
        )


@app.post("/upload_json")
async def upload_json(
    collection_name: str = Form(...), file: UploadFile = File(...)
) -> UploadJsonResponse:
    try:
        db_client = QdrantClient(location=QDRANT_URL)
        db_client.set_model(EMBEDDING_MODEL)
        db_client.set_sparse_model("Qdrant/bm25")
        create_collection_if_not_exists(db_client, collection_name)

        content = await file.read()
        try:
            data = json.loads(content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

        text = json.dumps(data, indent=2, ensure_ascii=False)
        vector = db_client.embed_model.embed(text)
        db_client.upsert(
            collection_name=collection_name,
            points=[
                rest.PointStruct(
                    id=file.filename,
                    vector=vector,
                    payload={"filename": file.filename, "content": text},
                )
            ],
        )
        return UploadJsonResponse(status="success", uploaded_count=1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload JSON: {str(e)}")


@app.post("/upload_document")
async def upload_document(
    collection_name: str = Form(...), file: UploadFile = File(...)
) -> UploadDocumentResponse:
    try:
        db_client = QdrantClient(location=QDRANT_URL)
        db_client.set_model(EMBEDDING_MODEL)
        db_client.set_sparse_model("Qdrant/bm25")
        create_collection_if_not_exists(db_client, collection_name)

        doc_converter = DocumentConverter(allowed_formats=[InputFormat.PDF])
        contents = await file.read()
        with open(f"/tmp/{file.filename}", "wb") as f:
            f.write(contents)
        result = doc_converter.convert(f"/tmp/{file.filename}")

        documents, metadatas = [], []
        for chunk in HybridChunker().chunk(result.document):
            documents.append(chunk.text)
            metadatas.append(chunk.meta.export_json_dict())

        db_client.add(
            collection_name=collection_name,
            documents=documents,
            metadata=metadatas,
            batch_size=64,
        )
        return UploadDocumentResponse(status="success", uploaded_count=len(documents))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@app.post("/upload_directory")
async def upload_directory(root_dir: str = Form(...), collection_name: str = Form(...)) -> UploadDirectoryResponse:
    db_client = QdrantClient(location=QDRANT_URL)
    db_client.set_model(EMBEDDING_MODEL)
    db_client.set_sparse_model("Qdrant/bm25")

    create_collection_if_not_exists(db_client, collection_name)

    uploaded = 0
    points = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    text = json.dumps(data, indent=2, ensure_ascii=False)
                    vector = db_client.embed_model.embed(text)
                    points.append(
                        rest.PointStruct(
                            id=f"{os.path.relpath(file_path, root_dir)}",  # unique ID per file
                            vector=vector,
                            payload={"filename": file, "path": file_path, "content": text},
                        )
                    )
                    uploaded += 1
                except Exception:
                    continue

    if points:
        db_client.upsert(collection_name=collection_name, points=points)

    return UploadDirectoryResponse(status="success", collections={collection_name: uploaded})

@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)
