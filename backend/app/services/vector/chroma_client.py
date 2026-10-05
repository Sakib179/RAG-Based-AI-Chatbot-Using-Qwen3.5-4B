"""Persistent ChromaDB client and collection management."""

from functools import lru_cache
from pathlib import Path
from typing import Any


CHROMA_DIRECTORY = Path(__file__).resolve().parents[3] / "chroma_db"
COLLECTION_NAME = "knowledge_base"


def _create_client() -> Any:
    """Create a persistent Chroma client only when first requested."""

    try:
        import chromadb
    except ImportError as exc:  # pragma: no cover - depends on installation
        raise RuntimeError("ChromaDB is not installed.") from exc

    CHROMA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIRECTORY))


@lru_cache(maxsize=1)
def get_chroma_client() -> Any:
    """Return the process-wide persistent Chroma client."""

    return _create_client()


def create_collection(name: str = COLLECTION_NAME) -> Any:
    """Create or return a cosine-similarity collection."""

    return get_chroma_client().get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def load_collection(name: str = COLLECTION_NAME) -> Any:
    """Load an existing collection without creating a new one."""

    return get_chroma_client().get_collection(name=name)


def get_collection(name: str = COLLECTION_NAME) -> Any:
    """Return the knowledge collection, creating it on first use."""

    return create_collection(name)


def get_vector_store(name: str = COLLECTION_NAME) -> Any:
    """Return the LlamaIndex adapter for the persistent Chroma collection."""

    try:
        from llama_index.vector_stores.chroma import ChromaVectorStore
    except ImportError as exc:  # pragma: no cover - depends on installation
        raise RuntimeError(
            "The LlamaIndex Chroma integration is not installed."
        ) from exc

    return ChromaVectorStore(chroma_collection=get_collection(name))


def persist_collection() -> None:
    """Persist vectors when supported by the installed Chroma client.

    ``PersistentClient`` writes changes automatically in current ChromaDB
    releases. The compatibility call keeps this boundary safe for older clients
    that expose an explicit ``persist`` method.
    """

    client = get_chroma_client()
    persist = getattr(client, "persist", None)
    if callable(persist):
        persist()
