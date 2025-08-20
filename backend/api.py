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
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from qdrant_client import QdrantClient
from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

from main import (
    DndKnowledgeBase,
    QDRANT_URL,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    SPARSE_MODEL,
)
from auth import get_user_context, UserContext
from chat_history import chat_history_manager

# Configuration
DND_HANDBOOK_URL = os.getenv(
    "DND_HANDBOOK_URL",
    "https://media.wizards.com/2014/downloads/dnd/PlayerDnDBasicRules_v0.2_PrintFriendly.pdf",
)
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "64"))

logfire.configure(
    token=os.environ["LOGFIRE_TOKEN"],
)
logfire.configure(scrubbing=False)
logfire.instrument_pydantic_ai()

app = FastAPI(
    title="D&D Knowledge Base API",
    description="API for answering Dungeons & Dragons 5th Edition questions",
    version="1.0.0",
)

# Add CORS middleware for frontend authentication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kb = DndKnowledgeBase()
main_agent = kb.get_main_agent()
intents_agent = kb.get_intents_agent()
deps = kb.get_deps()


class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    messages: List[dict]
    created_at: str
    updated_at: str


class CreateSessionRequest(BaseModel):
    title: str = ""


class UpdateSessionRequest(BaseModel):
    title: str


class DatabaseGenerationResponse(BaseModel):
    status: str
    document_count: int


class UserProfileResponse(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: str
    roles: list


class SavePartialResponseRequest(BaseModel):
    session_id: str
    partial_response: str


@app.get("/profile")
async def get_user_profile(
    user_context: UserContext = Depends(get_user_context),
) -> UserProfileResponse:
    """Get the current user's profile information."""
    return UserProfileResponse(
        user_id=user_context.user_id,
        username=user_context.username,
        email=user_context.email,
        full_name=user_context.full_name,
        roles=user_context.roles,
    )


@app.get("/chat/sessions")
async def get_chat_sessions(
    user_context: UserContext = Depends(get_user_context),
) -> List[ChatSessionResponse]:
    """Get all chat sessions for the current user."""
    sessions = await chat_history_manager.get_user_chat_sessions(user_context.user_id)

    return [
        ChatSessionResponse(
            id=session.id,
            title=session.title,
            messages=[msg.model_dump() for msg in session.messages],
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )
        for session in sessions
    ]


@app.post("/chat/sessions")
async def create_chat_session(
    request: CreateSessionRequest, user_context: UserContext = Depends(get_user_context)
) -> ChatSessionResponse:
    """Create a new chat session."""
    session = await chat_history_manager.create_chat_session(
        user_id=user_context.user_id, title=request.title
    )

    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        messages=[msg.model_dump() for msg in session.messages],
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


@app.get("/chat/sessions/{session_id}")
async def get_chat_session(
    session_id: str, user_context: UserContext = Depends(get_user_context)
) -> ChatSessionResponse:
    """Get a specific chat session."""
    session = await chat_history_manager.get_chat_session(
        session_id, user_context.user_id
    )

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        messages=[msg.model_dump() for msg in session.messages],
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


@app.put("/chat/sessions/{session_id}")
async def update_chat_session(
    session_id: str,
    request: UpdateSessionRequest,
    user_context: UserContext = Depends(get_user_context),
) -> dict:
    """Update a chat session"""
    success = await chat_history_manager.update_session_title(
        session_id, user_context.user_id, request.title
    )

    if not success:
        raise HTTPException(status_code=404, detail="Chat session not found")

    return {"message": "Session updated successfully"}


@app.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str, user_context: UserContext = Depends(get_user_context)
) -> dict:
    """Delete a chat session."""
    success = await chat_history_manager.delete_chat_session(
        session_id, user_context.user_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Chat session not found")

    return {"message": "Session deleted successfully"}


@app.post("/ask/stream")
async def ask_question_stream(
    request: QuestionRequest, user_context: UserContext = Depends(get_user_context)
) -> StreamingResponse:
    """Ask a D&D question with authentication required and save to chat history."""
    is_related = await intents_agent.run(request.question)

    if not is_related.output:

        async def error_generator():
            yield "Sorry, I can only answer questions related to Dungeons and Dragons 5th Edition."

        return StreamingResponse(error_generator(), media_type="text/plain")

    # Get chat history for context if session_id is provided
    message_history = []
    if request.session_id:
        session = await chat_history_manager.get_chat_session(
            request.session_id, user_context.user_id
        )
        if session:
            # Import Pydantic AI message types at runtime
            from pydantic_ai.messages import (
                ModelRequest,
                ModelResponse,
                UserPromptPart,
                TextPart,
            )

            # Convert MongoDB messages to Pydantic AI message format
            for msg in session.messages:
                if msg.is_user:
                    message_history.append(
                        ModelRequest(parts=[UserPromptPart(content=msg.content)])
                    )
                else:
                    message_history.append(
                        ModelResponse(parts=[TextPart(content=msg.content)])
                    )

        # Add the current question to history
        await chat_history_manager.add_message_to_session(
            request.session_id, user_context.user_id, request.question, is_user=True
        )

    async def stream_response():
        response_content = ""
        try:
            async with main_agent.iter(
                request.question, deps=deps, message_history=message_history
            ) as run:
                async for node in run:
                    if main_agent.is_model_request_node(node):
                        async with node.stream(run.ctx) as request_stream:
                            async for event in request_stream:
                                if hasattr(event, "delta") and hasattr(
                                    event.delta, "content_delta"
                                ):
                                    content_delta = event.delta.content_delta
                                    response_content += content_delta
                                    yield content_delta

            # Save complete response on successful completion
            if request.session_id and response_content:
                await chat_history_manager.add_message_to_session(
                    request.session_id,
                    user_context.user_id,
                    response_content,
                    is_user=False,
                )
        except Exception as e:
            # Save partial response with error indicator when an error occurs
            if request.session_id and response_content:
                error_message = (
                    f"\n\n❌ Error occurred during response generation: {str(e)}"
                )
                await chat_history_manager.add_message_to_session(
                    request.session_id,
                    user_context.user_id,
                    response_content + error_message,
                    is_user=False,
                )
            # Yield the error message to the stream
            yield f"\n\n❌ Error occurred: {str(e)}"

    return StreamingResponse(stream_response(), media_type="text/plain")


@app.post("/chat/save_partial")
async def save_partial_response(
    request: SavePartialResponseRequest,
    user_context: UserContext = Depends(get_user_context),
) -> dict:
    """Save a partial response when a stream is cancelled."""
    if not request.session_id or not request.partial_response:
        raise HTTPException(
            status_code=400, detail="Session ID and partial response are required"
        )

    success = await chat_history_manager.add_message_to_session(
        request.session_id,
        user_context.user_id,
        request.partial_response + "\n🛑 Response cancelled by user",
        is_user=False,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Chat session not found")

    return {"message": "Partial response saved successfully"}


@app.post("/generate_database")
async def generate_database(
    user_context: UserContext = Depends(get_user_context),
) -> DatabaseGenerationResponse:
    """Generate the D&D knowledge database. Requires authentication and admin role."""

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

        result = doc_converter.convert(DND_HANDBOOK_URL)

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
