"""
Baza wiedzy o PBŚ - Moduł główny (Obiektowy)

Ten moduł konfiguruje i inicjalizuje agenta wiedzy korzystając z pydantic-ai i Qdrant.
Zapewnie kluczową funkcjonalność retrievalu wiedzy z wektorowej bazy danych.
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


OLLAMA_URL = os.getenv("OLLAMA_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "documents")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant-api:6333")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


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
        self, collection_name: str, query_text: str, limit: int = 10
    ) -> list[str]:
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


class PbsKnowledgeBase:
    def __init__(self):
        self.qdrant_service = QdrantService()
        self.agent_factory = AgentFactory()
        self.main_agent, self.intents_agent = self.agent_factory.create_agents()
        self._register_tools()

    def _register_tools(self) -> None:
        @self.main_agent.tool
        async def retrieve(context: RunContext[Deps], search_query: str) -> str:
            """
            Narzędzie: retrieve

            Odpytuje lokalną wektorową baze danych (Qdrant) korzystając z zapewnionego search query.
            Zwraca tekst z dokumentów z bazy wiedzy.
            """
            results = self.qdrant_service.query_documents(COLLECTION_NAME, search_query)
            return "\n".join(results)


    def get_main_agent(self) -> Agent:
        return self.main_agent

    def get_intents_agent(self) -> Agent:
        return self.intents_agent

    def get_deps(self) -> Deps:
        return Deps(client=self.qdrant_service.client)
