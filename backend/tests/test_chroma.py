"""Unit tests for persistent Chroma collection management."""

from typing import Any

import pytest

from app.services.vector import chroma_client


class FakeCollection:
    """Small collection double for the client boundary."""


class FakeClient:
    def __init__(self) -> None:
        self.collection = FakeCollection()
        self.created_with: dict[str, Any] | None = None

    def get_or_create_collection(self, **kwargs: Any) -> FakeCollection:
        self.created_with = kwargs
        return self.collection

    def get_collection(self, **_: Any) -> FakeCollection:
        return self.collection


def test_chroma_collection_is_created_and_loaded(monkeypatch: Any) -> None:
    """The vector boundary creates and then loads the knowledge collection."""

    client = FakeClient()
    monkeypatch.setattr(chroma_client, "_create_client", lambda: client)
    chroma_client.get_chroma_client.cache_clear()

    created = chroma_client.create_collection()
    loaded = chroma_client.load_collection()

    assert created is client.collection
    assert loaded is client.collection
    assert client.created_with == {
        "name": "knowledge_base",
        "metadata": {"hnsw:space": "cosine"},
    }


def test_real_chroma_persists_a_vector(tmp_path: Any, monkeypatch: Any) -> None:
    """When installed, Chroma can persist and reload a knowledge vector."""

    pytest.importorskip("chromadb")
    monkeypatch.setattr(chroma_client, "CHROMA_DIRECTORY", tmp_path / "chroma_db")
    chroma_client.get_chroma_client.cache_clear()

    collection = chroma_client.create_collection("test_knowledge_base")
    collection.upsert(
        ids=["test-id"],
        documents=["A local knowledge fragment."],
        embeddings=[[1.0, 0.0]],
        metadatas=[{"filename": "test.txt", "document_type": "txt"}],
    )
    loaded = chroma_client.load_collection("test_knowledge_base")

    assert loaded.count() == 1
    assert loaded.get(ids=["test-id"])["documents"] == [
        "A local knowledge fragment."
    ]
    chroma_client.get_chroma_client.cache_clear()
