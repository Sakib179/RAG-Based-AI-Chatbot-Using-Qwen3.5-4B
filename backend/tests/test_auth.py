"""Tests for the protected authentication boundary."""

from fastapi.testclient import TestClient

from app.main import app


def test_authentication_is_required() -> None:
    """Protected routes return the stable authentication error envelope."""

    with TestClient(app) as client:
        response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {
        "success": False,
        "message": "Authentication failed",
    }
