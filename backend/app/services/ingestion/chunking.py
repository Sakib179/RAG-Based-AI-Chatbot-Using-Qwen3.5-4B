"""Recursive, metadata-preserving text chunking."""

from dataclasses import dataclass
from typing import Any

from app.services.ingestion.document_loader import LoadedDocument


DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 100
SEPARATORS = ("\n\n", "\n", ". ", " ", "")


@dataclass(frozen=True)
class TextChunk:
    """A chunk ready for embedding and vector storage."""

    text: str
    metadata: dict[str, Any]


def _split_recursively(
    text: str,
    chunk_size: int,
    separators: tuple[str, ...],
) -> list[str]:
    """Split text at the largest available semantic boundary."""

    if len(text) <= chunk_size:
        return [text]
    if not separators:
        return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]

    separator = separators[-1]
    for candidate in separators:
        if candidate == "" or candidate in text:
            separator = candidate
            break

    parts = text.split(separator) if separator else list(text)
    chunks: list[str] = []
    current = ""
    joiner = separator
    for part in parts:
        candidate = f"{current}{joiner}{part}" if current else part
        if current and len(candidate) > chunk_size:
            chunks.extend(_split_recursively(current, chunk_size, separators[1:]))
            current = part
        else:
            current = candidate
    if current:
        chunks.extend(_split_recursively(current, chunk_size, separators[1:]))
    return chunks


def recursive_chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Create overlapping chunks using paragraph-to-character boundaries."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size")

    normalized = text.strip()
    if not normalized:
        return []

    raw_chunks = [chunk.strip() for chunk in _split_recursively(normalized, chunk_size, SEPARATORS)]
    raw_chunks = [chunk for chunk in raw_chunks if chunk]
    if chunk_overlap == 0 or len(raw_chunks) <= 1:
        return raw_chunks

    chunks: list[str] = [raw_chunks[0]]
    for chunk in raw_chunks[1:]:
        previous = chunks[-1]
        overlap_length = min(chunk_overlap, max(0, chunk_size - len(chunk)))
        overlap = previous[-overlap_length:] if overlap_length else ""
        chunks.append(f"{overlap} {chunk}".strip())
    return chunks


def chunk_documents(
    documents: list[LoadedDocument],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """Chunk extracted documents while retaining source metadata."""

    chunks: list[TextChunk] = []
    for document in documents:
        for text in recursive_chunk_text(text=document.text, chunk_size=chunk_size, chunk_overlap=chunk_overlap):
            chunks.append(TextChunk(text=text, metadata=dict(document.metadata)))

    return chunks
