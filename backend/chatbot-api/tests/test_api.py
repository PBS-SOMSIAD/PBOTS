import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

with patch("main.QdrantService"):
    from api import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_ask_stream_missing_question():
    response = client.post("/ask/stream", json={})
    assert response.status_code == 422  # Walidacja pydantic
