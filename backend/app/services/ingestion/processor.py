"""Document indexing pipeline from source file to persistent Chroma vectors."""

from dataclasses import dataclass
import hashlib
import logging
from pathlib import Path
from typing import Any

from app.services.ai.embedding_service import get_embedding_model
from app.services.ingestion.chunking import TextChunk, chunk_documents
from app.services.ingestion.document_loader import load_document
from app.services.vector.chroma_client import get_collection, persist_collection

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IndexResult:
    """Summary of a document indexing operation."""

    source: str
    chunks_indexed: int


def _chunk_id(chunk: TextChunk, index: int) -> str:
    """Build a stable ID so re-indexing updates existing vectors."""

    source = str(chunk.metadata.get("source", "unknown"))
    digest = hashlib.sha256(
        f"{source}:{index}:{chunk.text}".encode("utf-8")
    ).hexdigest()
    return digest


def _embed_chunks(model: Any, chunks: list[TextChunk]) -> list[list[float]]:
    """Embed a batch when available, with a compatible single-item fallback."""

    texts = [chunk.text for chunk in chunks]
    if hasattr(model, "get_text_embedding_batch"):
        return model.get_text_embedding_batch(texts)
    return [model.get_text_embedding(text) for text in texts]


def _chroma_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """Remove unsupported ``None`` values before writing Chroma metadata."""

    return {
        key: value
        for key, value in metadata.items()
        if value is not None and isinstance(value, (str, int, float, bool))
    }


def _remove_existing_source(collection: Any, source: str) -> None:
    """Remove prior chunks so re-indexing cannot leave stale document text."""

    existing = collection.get(where={"source": source}, include=["metadatas"])
    existing_ids = existing.get("ids", [])
    if existing_ids:
        collection.delete(ids=existing_ids)


def process_document(path: str | Path) -> IndexResult:
    """Extract, chunk, embed, and persist one document without retraining."""

    source = str(path)
    documents = load_document(path)
    chunks = chunk_documents(documents)
    if not chunks:
        raise ValueError("The document does not contain extractable text.")

    embeddings = _embed_chunks(get_embedding_model(), chunks)
    collection = get_collection()
    _remove_existing_source(collection, source)
    collection.upsert(
        ids=[_chunk_id(chunk, index) for index, chunk in enumerate(chunks)],
        documents=[chunk.text for chunk in chunks],
        embeddings=embeddings,
        metadatas=[_chroma_metadata(chunk.metadata) for chunk in chunks],
    )
    persist_collection()
    logger.info("Indexed %s chunks from %s", len(chunks), source)
    return IndexResult(source=source, chunks_indexed=len(chunks))
