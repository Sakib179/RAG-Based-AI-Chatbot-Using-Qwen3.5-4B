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

    ollama_kwargs: dict[str, Any] = {
        "model": settings.ollama_model,
        "base_url": settings.ollama_base_url,
        "request_timeout": 120.0,
        "temperature": 0.0,
        "context_window": settings.ollama_context_window,
        "additional_kwargs": {"num_predict": settings.ollama_num_predict},
    }
    # keep_alive and thinking were added after older LlamaIndex Ollama
    # releases. Keep the project compatible with the pinned foundation while
    # enabling both controls whenever the installed adapter supports them.
    model_fields = getattr(Ollama, "model_fields", {}) or getattr(Ollama, "__fields__", {})
    if "keep_alive" in model_fields:
        ollama_kwargs["keep_alive"] = settings.ollama_keep_alive
    if "thinking" in model_fields:
        ollama_kwargs["thinking"] = settings.ollama_thinking
    return Ollama(**ollama_kwargs)
