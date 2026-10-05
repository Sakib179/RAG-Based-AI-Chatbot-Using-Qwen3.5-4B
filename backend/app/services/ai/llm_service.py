"""Lazy Ollama LLM configuration for LlamaIndex."""

from functools import lru_cache
from typing import Any

from app.core.config import settings


@lru_cache(maxsize=1)
def get_llm() -> Any:
    """Create and cache the local Qwen Ollama adapter.

    The adapter is constructed lazily so importing the API never contacts
    Ollama or allocates model memory. Actual generation happens only when a RAG
    query is executed.
    """

    try:
        from llama_index.llms.ollama import Ollama
    except ImportError as exc:  # pragma: no cover - depends on installation
        raise RuntimeError(
            "The Ollama LlamaIndex integration is not installed."
        ) from exc

    return Ollama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        request_timeout=120.0,
        temperature=0.0,
    )
