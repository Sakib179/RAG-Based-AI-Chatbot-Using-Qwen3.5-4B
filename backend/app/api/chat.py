"""Authenticated chat, conversation memory, and AI readiness endpoints."""

from dataclasses import dataclass, field
from time import perf_counter
from typing import Literal
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.database.repository import (
    create_conversation,
    get_conversation_history,
    list_conversations,
    save_log,
    save_messages,
)
from app.services.ai.embedding_service import embedding_dependency_available
from app.services.ai.llm_service import get_llm
from app.services.ai.rag_service import RagAnswer, query_knowledge_base
from app.services.auth.auth_dependency import get_current_user
from app.services.auth.auth_service import AuthenticatedUser
from app.services.vector.chroma_client import get_collection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4_000)
    conversation_id: str | None = Field(default=None, min_length=1, max_length=100)


class ChatSource(BaseModel):
    file: str
    pages: list[int] = Field(default_factory=list)
    similarity_percent: int = Field(ge=0, le=100)
    context: str | None = None


@dataclass
class _SourceAccumulator:
    pages: set[int] = field(default_factory=set)
    similarity: float = 0.0
    contexts: list[str] = field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    conversation_id: str
    response_time_ms: int


class ConversationSummary(BaseModel):
    id: str
    title: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ConversationMessage(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    sources: list[dict[str, object]] = Field(default_factory=list)
    created_at: str | None = None


class AIHealthResponse(BaseModel):
    llm: Literal["available", "unavailable"]
    vector_database: Literal["available", "unavailable"]
    embedding: Literal["available", "unavailable"]


def _source_response(result: RagAnswer) -> list[ChatSource]:
    grouped: dict[str, _SourceAccumulator] = {}
    for chunk in result.sources:
        filename = str(chunk.metadata.get("filename") or chunk.source)
        entry = grouped.setdefault(filename, _SourceAccumulator())
        page = chunk.metadata.get("page_number")
        if page is not None:
            try:
                entry.pages.add(int(page))
            except (TypeError, ValueError):
                logger.debug("Ignoring non-numeric page metadata for %s", filename)
        entry.similarity = max(entry.similarity, chunk.score)
        if chunk.text and chunk.text not in entry.contexts:
            entry.contexts.append(chunk.text)

    return [
        ChatSource(
            file=filename,
            pages=sorted(entry.pages),
            similarity_percent=round(entry.similarity * 100),
            context="\n\n".join(entry.contexts),
        )
        for filename, entry in grouped.items()
    ]


def _run_chat(
    request: ChatRequest,
    current_user: AuthenticatedUser,
) -> tuple[RagAnswer, str]:
    """Run blocking repository and local-model operations in one worker."""

    try:
        if request.conversation_id:
            conversation_id = request.conversation_id
            history = get_conversation_history(conversation_id, current_user.id, limit=10)
        else:
            conversation = create_conversation(current_user.id, request.question[:120])
            conversation_id = str(conversation["id"])
            history = []
    except Exception:
        logger.exception("Chat conversation lookup failed for user %s", current_user.id)
        raise

    try:
        result = query_knowledge_base(request.question, history)
    except Exception:
        logger.exception("Chat retrieval or LLM generation failed for user %s", current_user.id)
        raise
    source_payload = [
        {
            "file": source.file,
            "pages": source.pages,
            "similarity_percent": source.similarity_percent,
            "context": source.context,
        }
        for source in _source_response(result)
    ]
    try:
        save_messages(
            conversation_id,
            [
                {"role": "user", "content": request.question},
                {"role": "assistant", "content": result.answer, "sources": source_payload},
            ],
        )
    except Exception:
        logger.exception("Chat message persistence failed for user %s", current_user.id)
        raise
    return result, conversation_id


def _save_chat_log(
    user_id: str,
    request_data: dict[str, object],
    response_time: float,
    success: bool,
) -> None:
    """Keep a logging service failure from masking a successful answer."""

    try:
        save_log(user_id, "/api/chat", request_data, response_time, success)
    except Exception:
        logger.exception("Unable to persist chat request log")


@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask the knowledge base",
    description="Answer an authenticated user's question using retrieved local context and recent conversation memory.",
)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ChatResponse:
    started = perf_counter()
    try:
        result, conversation_id = await run_in_threadpool(_run_chat, request, current_user)
        response_time = perf_counter() - started
        background_tasks.add_task(
            _save_chat_log,
            current_user.id,
            {"question": request.question, "conversation_id": conversation_id},
            response_time,
            True,
        )
        return ChatResponse(
            answer=result.answer,
            sources=_source_response(result),
            conversation_id=conversation_id,
            response_time_ms=max(1, round(response_time * 1000)),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Knowledge-base query failed for user %s", current_user.id)
        await run_in_threadpool(
            _save_chat_log,
            current_user.id,
            {"question": request.question, "conversation_id": request.conversation_id},
            perf_counter() - started,
            False,
        )
        raise HTTPException(
            status_code=503,
            detail="Chat processing failed. Check backend logs for the failing stage.",
        ) from exc


@router.get(
    "/conversations",
    response_model=list[ConversationSummary],
    summary="List recent conversations",
    description="Return the authenticated user's persisted conversations, newest first.",
)
async def conversations(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[ConversationSummary]:
    rows = await run_in_threadpool(list_conversations, current_user.id, 20)
    return [ConversationSummary(**row) for row in rows]


@router.get(
    "/conversations/{conversation_id}",
    response_model=list[ConversationMessage],
    summary="Load a conversation",
    description="Return persisted messages for an owned conversation.",
)
async def conversation_messages(
    conversation_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[ConversationMessage]:
    rows = await run_in_threadpool(
        get_conversation_history, conversation_id, current_user.id, 100
    )
    return [ConversationMessage(**row) for row in rows]


def _component_status() -> AIHealthResponse:
    try:
        get_llm()
        llm_status: Literal["available", "unavailable"] = "available"
    except Exception:
        llm_status = "unavailable"

    try:
        get_collection()
        vector_status: Literal["available", "unavailable"] = "available"
    except Exception:
        vector_status = "unavailable"

    embedding_status: Literal["available", "unavailable"] = (
        "available" if embedding_dependency_available() else "unavailable"
    )
    return AIHealthResponse(
        llm=llm_status,
        vector_database=vector_status,
        embedding=embedding_status,
    )


@router.get(
    "/health",
    response_model=AIHealthResponse,
    summary="Check local AI service readiness",
    description="Checks local adapters without loading the embedding model into memory.",
)
async def chat_health() -> AIHealthResponse:
    return await run_in_threadpool(_component_status)
