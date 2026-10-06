"""Grounded answer generation over retrieved local knowledge."""

from dataclasses import dataclass, field
import logging
import re
from time import perf_counter
from typing import Any

from app.services.ai.llm_service import get_llm
from app.services.ai.prompts import FALLBACK_ANSWER, build_rag_prompt
from app.services.ai.retrieval_service import RetrievedChunk, retrieve_relevant_chunks

logger = logging.getLogger(__name__)
EXPLANATION_TERMS = {
    "explain", "summary", "summarize", "summarise", "describe", "compare",
    "details", "detailed", "steps", "list", "advantages", "disadvantages",
}


def _output_budget(question: str) -> int:
    """Choose a response budget without penalizing short factual questions."""

    normalized = question.lower()
    requested_words = re.search(r"\b(\d{2,4})\s+words?\b", normalized)
    if requested_words:
        return min(768, max(256, int(int(requested_words.group(1)) * 1.5)))
    if any(term in normalized for term in EXPLANATION_TERMS):
        return 512
    return 128


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

    retrieval_started = perf_counter()
    chunks = retrieve_relevant_chunks(question)
    logger.info(
        "RAG retrieval completed in %.2fs (%d chunks)",
        perf_counter() - retrieval_started,
        len(chunks),
    )
    if not chunks:
        return RagAnswer(answer=FALLBACK_ANSWER)

    prompt = build_rag_prompt(question.strip(), _format_context(chunks), history)
    generation_started = perf_counter()
    llm = get_llm()
    budget = _output_budget(question)
    try:
        response = llm.complete(prompt, num_predict=budget)
    except TypeError:
        # Test doubles and older LlamaIndex adapters may not expose the
        # per-request generation option.
        response = llm.complete(prompt)
    logger.info("Ollama generation completed in %.2fs", perf_counter() - generation_started)
    answer = _response_text(response)
    if not answer:
        logger.warning("The local LLM returned an empty answer")
        return RagAnswer(answer=FALLBACK_ANSWER, sources=chunks)

    return RagAnswer(answer=answer, sources=chunks)
