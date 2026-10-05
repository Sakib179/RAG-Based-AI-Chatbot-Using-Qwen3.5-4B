"""Unit tests for the local embedding adapter boundary."""

from types import ModuleType
from typing import Any

from app.services.ai import embedding_service


def test_embedding_model_loads_with_cpu_configuration(monkeypatch: Any) -> None:
    """The lazy adapter is cached after its first construction."""

    class FakeEmbedding:
        pass

    monkeypatch.setattr(embedding_service, "_build_embedding_model", lambda: FakeEmbedding())
    embedding_service.get_embedding_model.cache_clear()

    first = embedding_service.get_embedding_model()
    second = embedding_service.get_embedding_model()

    assert isinstance(first, FakeEmbedding)
    assert first is second


def test_embedding_model_factory_uses_local_bge_cpu(monkeypatch: Any) -> None:
    """The real factory passes the required model name and CPU device."""

    captured: dict[str, Any] = {}

    class FakeEmbedding:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    root_module = ModuleType("llama_index")
    embeddings_module = ModuleType("llama_index.embeddings")
    huggingface_module = ModuleType("llama_index.embeddings.huggingface")
    huggingface_module.HuggingFaceEmbedding = FakeEmbedding  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, "llama_index", root_module)
    monkeypatch.setitem(__import__("sys").modules, "llama_index.embeddings", embeddings_module)
    monkeypatch.setitem(
        __import__("sys").modules,
        "llama_index.embeddings.huggingface",
        huggingface_module,
    )

    model = embedding_service._build_embedding_model()

    assert isinstance(model, FakeEmbedding)
    assert captured == {"model_name": "BAAI/bge-m3", "device": "cpu"}
