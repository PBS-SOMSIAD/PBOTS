"""
PBS Knowledge Base - FastAPI Server

This module provides the FastAPI server implementation for the PBS knowledge base,
offering endpoints to ask questions and upload data to the vector database.

Example usage:

curl -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "Describe the spell Fireball in D&D 5e."}'

curl -X POST "http://localhost:8000/upload_json" \
  -F "collection_name=faq" \
  -F "file=@/path/to/file.json;type=application/json"

curl -X POST "http://localhost:8000/upload_document" \
  -F "collection_name=handbook" \
  -F "file=@/path/to/document.pdf;type=application/pdf"

curl -X POST "http://localhost:8000/upload_directory" \
  -F "root_dir=/path/to/data"

"""

import os
import logfire
import uvicorn
import httpx

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from main import PBSKnowledgeBase
from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str


if "LOGFIRE_TOKEN" in os.environ:
    logfire.configure(
        token=os.environ["LOGFIRE_TOKEN"],
    )
    logfire.instrument_pydantic_ai()

app = FastAPI(
    title="PBS Knowledge Base API",
    description="API for answering PBS questions",
    version="1.0.0",
)

kb = PBSKnowledgeBase()
main_agent = kb.get_main_agent()
intents_agent = kb.get_intents_agent()
deps = kb.get_deps()


@app.post("/ask/stream")
async def ask_question_stream(request: QuestionRequest) -> StreamingResponse:
    is_related = await intents_agent.run(request.question)

    if not is_related.output:

        async def error_generator():
            yield "Sorry, I can only answer questions related to PBS."

        return StreamingResponse(error_generator(), media_type="text/plain")

    async def stream_response():
        async with main_agent.iter(request.question, deps=deps) as run:
            async for node in run:
                if main_agent.is_model_request_node(node):
                    async with node.stream(run.ctx) as request_stream:
                        async for event in request_stream:
                            if hasattr(event, "delta") and hasattr(
                                event.delta, "content_delta"
                            ):
                                yield event.delta.content_delta

    return StreamingResponse(stream_response(), media_type="text/plain")


@app.post("/upload_json")
async def upload_json(collection_name: str = Form(...), file: UploadFile = File(...)

):
    async with httpx.AsyncClient() as client:
        files = {"file": (file.filename, await file.read(), file.content_type)}
        data = {"collection_name": collection_name}
        resp = await client.post("http://localhost:8001/upload_json", data=data, files=files)
        return resp.json()


@app.post("/upload_document")
async def upload_document(collection_name: str = Form(...), file: UploadFile = File(...)):
    async with httpx.AsyncClient() as client:
        files = {"file": (file.filename, await file.read(), file.content_type)}
        data = {"collection_name": collection_name}
        resp = await client.post("http://localhost:8001/upload_document", data=data, files=files)
        return resp.json()


@app.post("/upload_directory")
async def upload_directory(root_dir: str = Form(...)):
    async with httpx.AsyncClient() as client:
        data = {"root_dir": root_dir}
        resp = await client.post("http://localhost:8001/upload_directory", data=data)
        return resp.json()


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
