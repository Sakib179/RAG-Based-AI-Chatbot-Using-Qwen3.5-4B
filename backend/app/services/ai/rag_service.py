"""Grounded answer generation over retrieved local knowledge."""

from dataclasses import dataclass, field
import logging
from typing import Any

from app.services.ai.llm_service import get_llm
from app.services.ai.prompts import FALLBACK_ANSWER, build_rag_prompt
from app.services.ai.retrieval_service import RetrievedChunk, retrieve_relevant_chunks

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RagAnswer:
    """Answer text and the sources used to produce it."""

    answer: str
    sources: list[RetrievedChunk] = field(default_factory=list)


def _format_context(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks with source labels for the strict prompt."""

    return "\n\n".join(
        f"Source: {chunk.source}\n{chunk.text}" for chunk in chunks
    )


def _response_text(response: Any) -> str:
    """Extract text from a LlamaIndex completion response."""

    return str(getattr(response, "text", response)).strip()


def query_knowledge_base(
    question: str,
    history: list[dict[str, str]] | None = None,
) -> RagAnswer:
    """Retrieve grounded context and ask Qwen only when context is available."""

    chunks = retrieve_relevant_chunks(question)
    if not chunks:
        return RagAnswer(answer=FALLBACK_ANSWER)

    prompt = build_rag_prompt(question.strip(), _format_context(chunks), history)
    response = get_llm().complete(prompt)
    answer = _response_text(response)
    if not answer:
        logger.warning("The local LLM returned an empty answer")
        return RagAnswer(answer=FALLBACK_ANSWER, sources=chunks)

    return RagAnswer(answer=answer, sources=chunks)
