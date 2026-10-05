"""Retrieval of relevant chunks from the persistent Chroma collection."""

from dataclasses import dataclass, field
from typing import Any

from app.services.ai.embedding_service import get_embedding_model
from app.services.vector.chroma_client import get_collection


DEFAULT_TOP_K = 3
MIN_RELEVANCE_SCORE = 0.35


@dataclass(frozen=True)
class RetrievedChunk:
    """A retrieved document fragment and its source metadata."""

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0

    @property
    def source(self) -> str:
        """Return the most useful source identifier for this fragment."""

        return str(
            self.metadata.get("source")
            or self.metadata.get("filename")
            or "unknown"
        )


def _query_embedding(model: Any, question: str) -> list[float]:
    """Get a query vector across supported LlamaIndex embedding adapters."""

    if hasattr(model, "get_query_embedding"):
        return model.get_query_embedding(question)
    return model.get_text_embedding(question)


def retrieve_relevant_chunks(
    question: str,
    top_k: int = DEFAULT_TOP_K,
    min_score: float = MIN_RELEVANCE_SCORE,
) -> list[RetrievedChunk]:
    """Retrieve up to ``top_k`` chunks above the cosine-similarity threshold."""

    normalized_question = question.strip()
    if not normalized_question:
        return []

    collection = get_collection()
    collection_count = collection.count()
    if collection_count == 0:
        return []
    model = get_embedding_model()
    embedding = _query_embedding(model, normalized_question)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=min(max(1, top_k), collection_count),
        include=["documents", "metadatas", "distances"],
    )

    documents = (results.get("documents") or [[]])[0] or []
    metadatas = (results.get("metadatas") or [[]])[0] or []
    distances = (results.get("distances") or [[]])[0] or []

    chunks: list[RetrievedChunk] = []
    for index, document in enumerate(documents):
        if not document or not isinstance(document, str):
            continue
        distance = distances[index] if index < len(distances) else 1.0
        similarity = max(0.0, min(1.0, 1.0 - float(distance)))
        if similarity < min_score:
            continue
        metadata = metadatas[index] if index < len(metadatas) else {}
        chunks.append(
            RetrievedChunk(
                text=document,
                metadata=dict(metadata or {}),
                score=similarity,
            )
        )

    return chunks
