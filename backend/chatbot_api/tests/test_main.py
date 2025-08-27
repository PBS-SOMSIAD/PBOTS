import pytest
from unittest.mock import patch, MagicMock
from chatbot_api.main import DndKnowledgeBase, AgentFactory, QdrantService

def test_agent_factory_creates_agents():
    factory = AgentFactory()
    main_agent, intents_agent = factory.create_agents()
    assert main_agent is not None
    assert intents_agent is not None

@patch("chatbot_api.main.QdrantClient")
def test_qdrant_service_initialization(mock_qdrant_client):
    mock_instance = MagicMock()
    mock_qdrant_client.return_value = mock_instance
    service = QdrantService()
    assert service.client == mock_instance

@patch("chatbot_api.main.QdrantClient")
def test_dnd_knowledge_base_initialization(mock_qdrant_client):
    mock_instance = MagicMock()
    mock_qdrant_client.return_value = mock_instance
    kb = DndKnowledgeBase()
    assert kb.get_main_agent() is not None
    assert kb.get_intents_agent() is not None
    deps = kb.get_deps()
    assert hasattr(deps, "client")