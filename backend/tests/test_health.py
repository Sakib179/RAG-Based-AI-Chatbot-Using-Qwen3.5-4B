"""Tests for the public health endpoint."""

from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    """The health endpoint returns a healthy service response."""

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "AI Knowledge Chatbot Backend",
    }
