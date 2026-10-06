"""Chat response metadata and authenticated conversation history contracts."""

from datetime import datetime
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import chat as chat_api
from app.database import repository
from app.main import app
from app.services.ai.rag_service import RagAnswer
from app.services.ai.retrieval_service import RetrievedChunk
from app.services.auth.auth_dependency import get_current_user
from app.services.auth.auth_service import AuthenticatedUser


@pytest.fixture
def authenticated_client() -> Iterator[TestClient]:
    """Use a known identity without contacting Supabase Auth."""

    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id="user-a", email="user@example.com"
    )
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_chat_returns_timing_and_persists_source_excerpt(
    monkeypatch: Any, authenticated_client: TestClient
) -> None:
    """Source context survives storage; a logging failure cannot hide an answer."""

    saved: list[dict[str, Any]] = []
    excerpt = "Refunds are available within 30 days."
    chunk = RetrievedChunk(
        text=excerpt, metadata={"filename": "policy.pdf", "page_number": 5}
    )
    monkeypatch.setattr(
        chat_api, "create_conversation", lambda *args: {"id": "conversation-a"}
    )
    monkeypatch.setattr(
        chat_api, "query_knowledge_base", lambda *args: RagAnswer("**30 days**", [chunk])
    )
    monkeypatch.setattr(
        chat_api, "save_messages", lambda conversation_id, messages: saved.extend(messages)
    )

    def failed_log(*args: Any) -> None:
        raise RuntimeError("Logging is unavailable")

    monkeypatch.setattr(chat_api, "save_log", failed_log)
    response = authenticated_client.post("/api/chat", json={"question": "Refund policy?"})

    assert response.status_code == 200
    body = response.json()
    assert body["response_time_ms"] > 0
    assert body["conversation_id"] == "conversation-a"
    assert body["sources"] == [{
        "file": "policy.pdf",
        "pages": [5],
        "similarity_percent": 0,
        "context": excerpt,
    }]
    assert [message["role"] for message in saved] == ["user", "assistant"]
    assert saved[1]["sources"] == body["sources"]


def test_conversation_endpoints_use_authenticated_owner(
    monkeypatch: Any, authenticated_client: TestClient
) -> None:
    """Both history operations receive the signed-in user's identity."""

    calls: list[tuple[Any, ...]] = []

    def list_owned(user_id: str, limit: int) -> list[dict[str, Any]]:
        calls.append((user_id, limit))
        return [{"id": "conversation-a", "title": "Refund policy"}]

    def load_owned(conversation_id: str, user_id: str, limit: int) -> list[dict[str, Any]]:
        calls.append((conversation_id, user_id, limit))
        return [{"id": "message-a", "conversation_id": conversation_id,
                 "role": "assistant", "content": "**30 days**", "sources": []}]

    monkeypatch.setattr(chat_api, "list_conversations", list_owned)
    monkeypatch.setattr(chat_api, "get_conversation_history", load_owned)
    listing = authenticated_client.get("/api/chat/conversations")
    history = authenticated_client.get("/api/chat/conversations/conversation-a")

    assert listing.status_code == history.status_code == 200
    assert listing.json()[0]["title"] == "Refund policy"
    assert history.json()[0]["content"] == "**30 days**"
    assert calls == [("user-a", 20), ("conversation-a", "user-a", 100)]


def test_conversation_endpoints_require_authentication() -> None:
    with TestClient(app) as client:
        assert client.get("/api/chat/conversations").status_code == 401
        assert client.get("/api/chat/conversations/conversation-a").status_code == 401


def test_message_batch_uses_one_insert_with_stable_order(monkeypatch: Any) -> None:
    """A batched exchange remains ordered when loaded by creation timestamp."""

    inserts: list[list[dict[str, Any]]] = []

    class FakeClient:
        def table(self, name: str) -> "FakeClient":
            assert name == "messages"
            return self

        def insert(self, payload: list[dict[str, Any]]) -> "FakeClient":
            inserts.append(payload)
            return self

        def execute(self) -> SimpleNamespace:
            return SimpleNamespace(data=inserts[-1])

    monkeypatch.setattr(repository, "get_supabase_client", FakeClient)
    rows = repository.save_messages("conversation-a", [
        {"role": "user", "content": "Refund policy?"},
        {"role": "assistant", "content": "30 days"},
    ])

    assert len(inserts) == 1
    assert [row["role"] for row in rows] == ["user", "assistant"]
    assert datetime.fromisoformat(rows[0]["created_at"]) < datetime.fromisoformat(rows[1]["created_at"])
