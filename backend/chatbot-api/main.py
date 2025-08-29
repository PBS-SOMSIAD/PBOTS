"""
PBS Knowledge Base - Main Module (Object-Oriented)

This module configures and initializes the PBS knowledge agent using pydantic-ai and Qdrant.
It provides core functionality for retrieving PBS information from a vector database and web.
"""

import os
from dataclasses import dataclass
from typing import Tuple

import system_prompts
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from qdrant_client import QdrantClient

from web_search import WebSearchTool

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
MODEL_NAME = "qwen3:1.7b"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "baza"


class WebSearchResult(BaseModel):
    url: str
    content: str


@dataclass
class Deps:
    client: QdrantClient


class QdrantService:
    def __init__(self, url: str = QDRANT_URL, embedding_model: str = EMBEDDING_MODEL):
        self.client = QdrantClient(location=url)
        try:
            self.client.set_model(embedding_model)
            self.client.set_sparse_model("Qdrant/bm25")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Qdrant client: {e}") from e

    def query_documents(
        self, query_text: str, doc_type: str = None, limit: int = 10
    ) -> list[str]:
        # Query tylko z jednej kolekcji 'baza', opcjonalnie filtr po doc_type
        filter_payload = None
        if doc_type:
            filter_payload = {"doc_type": doc_type}
        points = self.client.query(
            collection_name=COLLECTION_NAME,
            query_text=query_text,
            limit=limit,
            query_filter=filter_payload
        )
        # Zwróć content i typ dokumentu
        return [f"\n[{point.payload.get('doc_type', 'unknown')}] {point.payload.get('content', '')}\n" for point in points]


class AgentFactory:
    def __init__(self, model_name: str = MODEL_NAME, base_url: str = OLLAMA_URL):
        self.model = OpenAIModel(
            model_name=model_name, provider=OpenAIProvider(base_url=base_url)
        )

    def create_agents(self) -> Tuple[Agent, Agent, Agent]:
        main_agent = Agent(
            model=self.model,
            deps_type=Deps,
            output_type=str,
            system_prompt=system_prompts.MAIN_SYSTEM_PROMPT,
        )

        intents_agent = Agent(
            model=self.model,
            output_type=bool,
            system_prompt=system_prompts.INTENT_SYSTEM_PROMPT,
        )

        return main_agent, intents_agent


class PBSKnowledgeBase:
    def __init__(self):
        self.qdrant_service = QdrantService()
        self.agent_factory = AgentFactory()
        self.web_tool = WebSearchTool()
        self.main_agent, self.intents_agent = self.agent_factory.create_agents()
        self._register_tools()

    def _register_tools(self) -> None:
        @self.main_agent.tool
        async def retrieve(
            context: RunContext[Deps], search_query: str, doc_type: str = None
        ) -> str:
            """
            Tool: retrieve

            Queries the local vector database (Qdrant) using the provided search query and optional doc_type.
            Returns a concatenated string of relevant documents from the PBS knowledge base.
            """
            results = self.qdrant_service.query_documents(search_query, doc_type=doc_type)
            return "\n".join(results)

        @self.main_agent.tool
        async def web_search(
            context: RunContext[Deps], search_query: str
        ) -> WebSearchResult:
            """
            Tool: web_search

            Description:
            Performs a live Google search for the given query and scrapes the content
            of the top result. Returns both the URL and the extracted page content.
            """
            search_result = self.web_tool.web_search(query=search_query, max_results=1)
            url = search_result.results[0].url
            content = self.web_tool.web_scrap(url)
            return WebSearchResult(url=url, content=content)

        @self.main_agent.tool
        async def list_doc_types(context: RunContext[Deps]) -> str:
            """
            Tool: list_doc_types

            Lists available document types in the knowledge base.
            """
            return "FAQ, Rekrutacja, Pracownicy, Aktualności"

    def get_main_agent(self) -> Agent:
        return self.main_agent

    def get_intents_agent(self) -> Agent:
        return self.intents_agent

    def get_deps(self) -> Deps:
        return Deps(client=self.qdrant_service.client)
