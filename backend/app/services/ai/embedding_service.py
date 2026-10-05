"""Lazy local BGE-M3 embedding configuration."""

from functools import lru_cache
import importlib.util
from typing import Any


EMBEDDING_MODEL_NAME = "BAAI/bge-m3"


def _build_embedding_model() -> Any:
    """Build the CPU embedding adapter without requiring GPU support."""

    try:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    except ImportError as exc:  # pragma: no cover - depends on installation
        raise RuntimeError(
            "The HuggingFace LlamaIndex integration is not installed."
        ) from exc

    return HuggingFaceEmbedding(
        model_name=EMBEDDING_MODEL_NAME,
        device="cpu",
    )


@lru_cache(maxsize=1)
def get_embedding_model() -> Any:
    """Load and cache BGE-M3 on first use."""

    return _build_embedding_model()


def embedding_dependency_available() -> bool:
    """Return whether the local embedding integration can be imported."""

    try:
        return importlib.util.find_spec("llama_index.embeddings.huggingface") is not None
    except ModuleNotFoundError:
        return False
