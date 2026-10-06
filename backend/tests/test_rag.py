"""Unit tests for retrieval thresholding and grounded answer generation."""

from typing import Any

from app.services.ai import rag_service
from app.services.ai.prompts import FALLBACK_ANSWER
from app.services.ai.prompts import build_rag_prompt
from app.services.ai import retrieval_service
from app.services.ai.retrieval_service import RetrievedChunk


class FakeResponse:
    text = "The refund window is 30 days."


class FakeLLM:
    def __init__(self) -> None:
        self.prompt = ""

    def complete(self, prompt: str) -> FakeResponse:
        self.prompt = prompt
        return FakeResponse()


def test_rag_uses_retrieved_context_and_returns_sources(monkeypatch: Any) -> None:
    """Generation receives source context and returns its metadata."""

    chunk = RetrievedChunk(
        text="Refunds are available within 30 days.",
        metadata={"filename": "policy.pdf", "page_number": 5, "source": "policy.pdf"},
        score=0.9,
    )
    llm = FakeLLM()
    monkeypatch.setattr(rag_service, "retrieve_relevant_chunks", lambda _: [chunk])
    monkeypatch.setattr(rag_service, "get_llm", lambda: llm)

    result = rag_service.query_knowledge_base("What is the refund policy?")

    assert result.answer == "The refund window is 30 days."
    assert result.sources == [chunk]
    assert "Refunds are available within 30 days." in llm.prompt
    assert "Do not use outside knowledge." in llm.prompt


def test_chat_sources_group_chunks_by_file_and_page(monkeypatch: Any) -> None:
    """One source entry contains all pages and the strongest chunk score."""

    from app.api.chat import _source_response

    result = rag_service.RagAnswer(
        answer="answer",
        sources=[
            RetrievedChunk("first", {"filename": "guide.pdf", "page_number": 1}, 0.61),
            RetrievedChunk("second", {"filename": "guide.pdf", "page_number": 3}, 0.87),
            RetrievedChunk("duplicate", {"filename": "guide.pdf", "page_number": 1}, 0.40),
        ],
    )

    assert _source_response(result)[0].model_dump() == {
        "file": "guide.pdf",
        "pages": [1, 3],
        "similarity_percent": 87,
        "context": "first\n\nsecond\n\nduplicate",
    }


def test_rag_falls_back_without_retrieved_context(monkeypatch: Any) -> None:
    """Qwen is not called when retrieval returns no relevant chunks."""

    monkeypatch.setattr(rag_service, "retrieve_relevant_chunks", lambda _: [])

    class FailingLLM:
        def complete(self, _: str) -> None:
            raise AssertionError("LLM must not be called without context")

    monkeypatch.setattr(rag_service, "get_llm", lambda: FailingLLM())

    result = rag_service.query_knowledge_base("Unknown question")

    assert result.answer == FALLBACK_ANSWER
    assert result.sources == []


def test_retrieval_returns_only_chunks_above_threshold(monkeypatch: Any) -> None:
    """Chroma distances are converted to cosine similarity and filtered."""

    class FakeCollection:
        def count(self) -> int:
            return 2

        def query(self, **_: Any) -> dict[str, list[list[Any]]]:
            return {
                "documents": [["relevant", "irrelevant"]],
                "metadatas": [[{"filename": "policy.txt"}, {"filename": "other.txt"}]],
                "distances": [[0.1, 0.9]],
            }

    class FakeEmbedding:
        def get_query_embedding(self, _: str) -> list[float]:
            return [1.0, 0.0]

    monkeypatch.setattr(retrieval_service, "get_collection", lambda: FakeCollection())
    monkeypatch.setattr(retrieval_service, "get_embedding_model", lambda: FakeEmbedding())

    chunks = retrieval_service.retrieve_relevant_chunks("policy", top_k=3)

    assert [chunk.text for chunk in chunks] == ["relevant"]
    assert chunks[0].metadata["filename"] == "policy.txt"


def test_prompt_bounds_history_without_truncating_document_context() -> None:
    """Large previous answers do not inflate every subsequent generation."""

    context = "Document facts " * 500
    prompt = build_rag_prompt("Current question", context, [
        {"role": "user", "content": "Older question"},
        {"role": "assistant", "content": "A" * 10_000},
        {"role": "user", "content": "Most recent question"},
    ])

    assert context in prompt
    assert "Most recent question" in prompt
    assert "Older question" not in prompt
    assert len(prompt) < len(context) + 5_000
