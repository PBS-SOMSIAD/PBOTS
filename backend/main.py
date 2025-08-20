"""
D&D Knowledge Base - Main Module (Object-Oriented)

This module configures and initializes the D&D knowledge agent using pydantic-ai and Qdrant.
It provides core functionality for retrieving D&D information from a vector database and web.
"""

import os
from dataclasses import dataclass
from typing import Tuple

import system_prompts
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from qdrant_client import QdrantClient

from web_search import WebSearchTool
from web_search import SearchResult

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3:1.7b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "handbook")
SPARSE_MODEL = os.getenv("SPARSE_MODEL", "Qdrant/bm25")
QUERY_LIMIT = int(os.getenv("QUERY_LIMIT", "10"))


@dataclass
class Deps:
    client: QdrantClient


class QdrantService:
    def __init__(self, url: str = QDRANT_URL, embedding_model: str = EMBEDDING_MODEL):
        self.client = QdrantClient(location=url)
        try:
            self.client.set_model(embedding_model)
            self.client.set_sparse_model(SPARSE_MODEL)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Qdrant client: {e}") from e

    def query_documents(
        self, collection_name: str, query_text: str, limit: int = None
    ) -> list[str]:
        limit = limit or QUERY_LIMIT
        points = self.client.query(
            collection_name=collection_name,
            query_text=query_text,
            limit=limit,
        )
        return [f"\n{point.document}\n" for point in points]


class AgentFactory:
    def __init__(self, model_name: str = MODEL_NAME, base_url: str = OLLAMA_URL):
        self.model = OpenAIModel(
            model_name=model_name, provider=OpenAIProvider(base_url=base_url)
        )

    def create_agents(self) -> Tuple[Agent, Agent]:
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


class DndKnowledgeBase:
    def __init__(self):
        self.qdrant_service = QdrantService()
        self.agent_factory = AgentFactory()
        self.web_tool = WebSearchTool()
        self.main_agent, self.intents_agent = self.agent_factory.create_agents()
        self._register_tools()

    def _register_tools(self) -> None:
        @self.main_agent.tool
        async def retrieve(context: RunContext[Deps], search_query: str) -> str:
            """
            Tool: retrieve

            Queries the local vector database (Qdrant) using the provided search query.
            Returns a concatenated string of relevant documents from the D&D 5e knowledge base.
            """
            results = self.qdrant_service.query_documents(COLLECTION_NAME, search_query)
            return "\n".join(results)

        @self.main_agent.tool
        async def web_search(
            context: RunContext[Deps], search_query: str
        ) -> SearchResult:
            """
            Tool: web_search

            Description:
            Performs a live Google search for the given query and scrapes the content
            of the top result. Returns both the URL and the extracted page content.
            """
            response = await self.web_tool.search_and_scrape(query=search_query)
            if not response.results:
                return SearchResult(
                    url="",
                    title="No result",
                    snippet="",
                    scraped_content=f"No valid search results found for query: {search_query}",
                )
            print(response.results[0], flush=True)
            return response.results[0]

    def get_main_agent(self) -> Agent:
        return self.main_agent

    def get_intents_agent(self) -> Agent:
        return self.intents_agent

    def get_deps(self) -> Deps:
        return Deps(client=self.qdrant_service.client)
