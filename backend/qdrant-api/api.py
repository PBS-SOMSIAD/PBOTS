import uvicorn
import os
import json
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter
from sentence_transformers import SentenceTransformer


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


def create_collection_if_not_exists(client, collection_name="baza", dim=384):
    if collection_name not in [c.name for c in client.get_collections().collections]:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=rest.VectorParams(size=dim, distance=rest.Distance.COSINE),
        )


@app.post("/upload_json")
async def upload_json(file: UploadFile = File(...), doc_type: str = Form("unknown")) -> UploadJsonResponse:
    """
    Dodaje JSON do kolekcji 'baza'.
    doc_type: typ dokumentu (FAQ, Rekrutacja, Pracownicy, Aktualności, ...)
    """
    try:
        db_client = QdrantClient(location=QDRANT_URL)
        create_collection_if_not_exists(db_client, "baza")

        # Załaduj model embeddingu
        model = SentenceTransformer(EMBEDDING_MODEL)

        content = await file.read()
        try:
            data = json.loads(content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

        text = json.dumps(data, indent=2, ensure_ascii=False)
        vector = model.encode(text).tolist()
        db_client.upsert(
            collection_name="baza",
            points=[
                rest.PointStruct(
                    id=str(uuid.uuid4()),  # <-- generuj UUID
                    vector=vector,
                    payload={"filename": file.filename, "content": text, "doc_type": doc_type},
                )
            ],
        )
        return UploadJsonResponse(status="success", uploaded_count=1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload JSON: {str(e)}")


@app.post("/upload_document")
async def upload_document(file: UploadFile = File(...), doc_type: str = Form("unknown")) -> UploadDocumentResponse:
    """
    Dodaje dokument PDF do kolekcji 'baza'.
    doc_type: typ dokumentu
    """
    try:
        db_client = QdrantClient(location=QDRANT_URL)
        db_client.set_model(EMBEDDING_MODEL)
        db_client.set_sparse_model("Qdrant/bm25")
        create_collection_if_not_exists(db_client, "baza")

        doc_converter = DocumentConverter(allowed_formats=[InputFormat.PDF])
        contents = await file.read()
        tmp_path = f"/tmp/{file.filename}"
        with open(tmp_path, "wb") as f:
            f.write(contents)
        result = doc_converter.convert(tmp_path)

        documents, metadatas = [], []
        for chunk in HybridChunker().chunk(result.document):
            documents.append(chunk.text)
            metadatas.append(chunk.meta.export_json_dict())

        # Embedding i upload do jednej kolekcji
        for doc, meta in zip(documents, metadatas):
            vector = db_client.embed_model.embed(doc)
            if hasattr(vector, "tolist"):
                vector = vector.tolist()
            db_client.upsert(
                collection_name="baza",
                points=[
                    rest.PointStruct(
                        id=str(uuid.uuid4()) + f"_{meta.get('chunk_id', '')}",
                        vector=vector,
                        payload={"filename": file.filename, "content": doc, "doc_type": doc_type, "meta": meta},
                    )
                ],
            )
        return UploadDocumentResponse(status="success", uploaded_count=len(documents))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@app.post("/upload_directory")
async def upload_directory(root_dir: str = Form(...), doc_type: str = Form("unknown")) -> UploadDirectoryResponse:
    """
    Rekurencyjny upload wszystkich JSON-ów z folderu do kolekcji 'baza'.
    doc_type: typ dokumentu
    """
    db_client = QdrantClient(location=QDRANT_URL)
    db_client.set_model(EMBEDDING_MODEL)
    db_client.set_sparse_model("Qdrant/bm25")
    create_collection_if_not_exists(db_client, "baza")
    uploaded = 0
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    text = json.dumps(data, indent=2, ensure_ascii=False)
                    vector = db_client.embed_model.embed(text)
                    db_client.upsert(
                        collection_name="baza",
                        points=[
                            rest.PointStruct(
                                id=file,
                                vector=vector,
                                payload={"filename": file, "content": text, "doc_type": doc_type, "path": file_path},
                            )
                        ],
                    )
                    uploaded += 1
                except Exception:
                    continue
    return UploadDirectoryResponse(status="success", collections={"baza": uploaded})


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)
