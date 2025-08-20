"""
D&D Knowledge Base - FastAPI Server

This module provides the FastAPI server implementation for the D&D knowledge base,
offering endpoints to ask questions and generate the vector database.

Example usage:

curl -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "Describe the spell Fireball in D&D 5e."}'

curl -X POST http://localhost:8000/generate_database
"""

import os
import logfire
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from qdrant_client import QdrantClient
from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

from main import (
    DndKnowledgeBase,
    QDRANT_URL,
    COLLECTION_NAME,
    EMBEDDING_MODEL
)

logfire.configure(token=os.environ['LOGFIRE_TOKEN'],)
logfire.instrument_pydantic_ai()

app = FastAPI(
    title="D&D Knowledge Base API",
    description="API for answering Dungeons & Dragons 5th Edition questions",
    version="1.0.0"
)

kb = DndKnowledgeBase()
main_agent = kb.get_main_agent()
intents_agent = kb.get_intents_agent()
deps = kb.get_deps()


class QuestionRequest(BaseModel):
    question: str


class DatabaseGenerationResponse(BaseModel):
    status: str
    document_count: int


@app.post("/ask/stream")
async def ask_question_stream(request: QuestionRequest) -> StreamingResponse:
    is_related = await intents_agent.run(request.question)

    if not is_related.output:
        async def error_generator():
            yield "Sorry, I can only answer questions related to Dungeons and Dragons 5th Edition."
        return StreamingResponse(error_generator(), media_type="text/plain")

    async def stream_response():
        async with main_agent.iter(request.question, deps=deps) as run:
            async for node in run:
                if main_agent.is_model_request_node(node):
                    async with node.stream(run.ctx) as request_stream:
                        async for event in request_stream:
                            if hasattr(event, "delta") and hasattr(event.delta, "content_delta"):
                                yield event.delta.content_delta

    return StreamingResponse(stream_response(), media_type="text/plain")


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
            status="success",
            document_count=len(documents)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate database: {str(e)}"
        )

@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
