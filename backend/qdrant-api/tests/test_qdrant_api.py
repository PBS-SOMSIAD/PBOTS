from fastapi.testclient import TestClient
import pytest
from api import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_generate_database():
    response = client.post("/generate_database")
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert "document_count" in data
        assert isinstance(data["document_count"], int)
        return data
    else:
        print(f"Error: {response.status_code}, Detail: {response.json()}")
        assert response.status_code == 500  # Expected failure case     return None
        assert "Failed to generate database" in response.json().get("detail", "")



