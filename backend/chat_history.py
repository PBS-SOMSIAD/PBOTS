"""
Chat History Management Module

This module handles storing and retrieving user chat histories using MongoDB.
"""

import os
from datetime import datetime, timezone
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from bson import ObjectId

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:password@localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "dnd_rag")


def utc_now() -> datetime:
    """Helper function to get current UTC datetime."""
    return datetime.now(timezone.utc)


class ChatMessage(BaseModel):
    """Represents a single message in a chat."""

    id: Optional[str] = None
    content: str
    is_user: bool
    timestamp: datetime = Field(default_factory=utc_now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ChatSession(BaseModel):
    """Represents a chat session."""

    id: Optional[str] = None
    user_id: str
    title: str = ""
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ChatHistoryManager:
    """Manages chat histories in MongoDB."""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.chat_sessions = None

    async def connect(self):
        """Connect to MongoDB."""
        if self.client is None:
            self.client = AsyncIOMotorClient(MONGODB_URL)
            self.db = self.client[MONGODB_DATABASE]
            self.chat_sessions = self.db.chat_sessions

            await self._create_indexes()

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self.client = None

    async def _create_indexes(self):
        """Create necessary indexes for chat sessions."""
        # Index on user_id for fast user queries
        await self.chat_sessions.create_index("user_id")

        # Index on user_id and updated_at for sorting user chats
        await self.chat_sessions.create_index([("user_id", 1), ("updated_at", -1)])

        # Index on created_at for general sorting
        await self.chat_sessions.create_index("created_at")

    async def create_chat_session(self, user_id: str, title: str = "") -> ChatSession:
        """Create a new chat session for a user."""
        await self.connect()

        chat_session = ChatSession(
            user_id=user_id,
            title=title,
            messages=[],
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        # Convert to dict for MongoDB
        session_dict = chat_session.model_dump(exclude={"id"})
        result = await self.chat_sessions.insert_one(session_dict)

        # Set the ID and return
        chat_session.id = str(result.inserted_id)
        return chat_session

    async def get_user_chat_sessions(
        self, user_id: str, limit: int = 50
    ) -> List[ChatSession]:
        """Get all chat sessions for a user, ordered by most recent."""
        await self.connect()

        cursor = (
            self.chat_sessions.find({"user_id": user_id})
            .sort("updated_at", -1)
            .limit(limit)
        )

        sessions = []
        async for doc in cursor:
            # Convert ObjectId to string
            doc["id"] = str(doc["_id"])
            del doc["_id"]

            # Convert message timestamps
            for message in doc.get("messages", []):
                if isinstance(message.get("timestamp"), datetime):
                    message["timestamp"] = message["timestamp"]
                else:
                    # Parse string timestamp if needed
                    try:
                        message["timestamp"] = datetime.fromisoformat(
                            message["timestamp"].replace("Z", "+00:00")
                        )
                    except (ValueError, AttributeError):
                        message["timestamp"] = utc_now()

            sessions.append(ChatSession(**doc))

        return sessions

    async def get_chat_session(
        self, session_id: str, user_id: str
    ) -> Optional[ChatSession]:
        """Get a specific chat session by ID, ensuring it belongs to the user."""
        await self.connect()

        try:
            doc = await self.chat_sessions.find_one(
                {"_id": ObjectId(session_id), "user_id": user_id}
            )

            if not doc:
                return None

            # Convert ObjectId to string
            doc["id"] = str(doc["_id"])
            del doc["_id"]

            # Convert message timestamps
            for message in doc.get("messages", []):
                if isinstance(message.get("timestamp"), datetime):
                    message["timestamp"] = message["timestamp"]
                else:
                    try:
                        message["timestamp"] = datetime.fromisoformat(
                            message["timestamp"].replace("Z", "+00:00")
                        )
                    except (ValueError, AttributeError):
                        message["timestamp"] = utc_now()

            return ChatSession(**doc)

        except Exception:
            return None

    async def add_message_to_session(
        self, session_id: str, user_id: str, content: str, is_user: bool
    ) -> bool:
        """Add a message to a chat session."""
        await self.connect()

        try:
            message = ChatMessage(content=content, is_user=is_user, timestamp=utc_now())

            # Update the session with the new message and updated timestamp
            result = await self.chat_sessions.update_one(
                {"_id": ObjectId(session_id), "user_id": user_id},
                {
                    "$push": {"messages": message.model_dump()},
                    "$set": {"updated_at": utc_now()},
                },
            )

            return result.modified_count > 0

        except Exception:
            return False

    async def update_session_title(
        self, session_id: str, user_id: str, title: str
    ) -> bool:
        """Update the title of a chat session."""
        await self.connect()

        try:
            result = await self.chat_sessions.update_one(
                {"_id": ObjectId(session_id), "user_id": user_id},
                {"$set": {"title": title, "updated_at": utc_now()}},
            )

            return result.modified_count > 0

        except Exception:
            return False

    async def delete_chat_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session."""
        await self.connect()

        try:
            result = await self.chat_sessions.delete_one(
                {"_id": ObjectId(session_id), "user_id": user_id}
            )

            return result.deleted_count > 0

        except Exception:
            return False

    async def update_session_messages(
        self, session_id: str, user_id: str, messages: List[ChatMessage]
    ) -> bool:
        """Update all messages in a session (useful for bulk updates)."""
        await self.connect()

        try:
            result = await self.chat_sessions.update_one(
                {"_id": ObjectId(session_id), "user_id": user_id},
                {
                    "$set": {
                        "messages": [msg.model_dump() for msg in messages],
                        "updated_at": utc_now(),
                    }
                },
            )

            return result.modified_count > 0

        except Exception:
            return False


chat_history_manager = ChatHistoryManager()
