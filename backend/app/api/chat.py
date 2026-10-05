"""Authenticated chat, conversation memory, and AI readiness endpoints."""

from time import perf_counter
from typing import Literal
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.database.repository import (
    create_conversation,
    get_conversation_history,
    save_log,
    save_message,
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
    page: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    conversation_id: str


class AIHealthResponse(BaseModel):
    llm: Literal["available", "unavailable"]
    vector_database: Literal["available", "unavailable"]
    embedding: Literal["available", "unavailable"]


def _source_response(result: RagAnswer) -> list[ChatSource]:
    return [
        ChatSource(
            file=str(chunk.metadata.get("filename") or chunk.source),
            page=chunk.metadata.get("page_number"),
        )
        for chunk in result.sources
    ]


def _run_chat(
    request: ChatRequest,
    current_user: AuthenticatedUser,
) -> tuple[RagAnswer, str]:
    """Run blocking repository and local-model operations in one worker."""

    if request.conversation_id:
        conversation_id = request.conversation_id
        history = get_conversation_history(conversation_id, current_user.id, limit=10)
    else:
        conversation = create_conversation(current_user.id, request.question[:120])
        conversation_id = str(conversation["id"])
        history = []

    result = query_knowledge_base(request.question, history)
    source_payload = [
        {"file": source.file, "page": source.page} for source in _source_response(result)
    ]
    save_message(conversation_id, "user", request.question)
    save_message(conversation_id, "assistant", result.answer, source_payload)
    return result, conversation_id


@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask the knowledge base",
    description="Answer an authenticated user's question using retrieved local context and recent conversation memory.",
)
async def chat(
    request: ChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ChatResponse:
    started = perf_counter()
    success = False
    try:
        result, conversation_id = await run_in_threadpool(_run_chat, request, current_user)
        success = True
        return ChatResponse(
            answer=result.answer,
            sources=_source_response(result),
            conversation_id=conversation_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Knowledge-base query failed for user %s", current_user.id)
        raise HTTPException(
            status_code=503,
            detail="The knowledge-base service is unavailable.",
        ) from exc
    finally:
        try:
            await run_in_threadpool(
                save_log,
                current_user.id,
                "/api/chat",
                {"question": request.question, "conversation_id": request.conversation_id},
                perf_counter() - started,
                success,
            )
        except Exception:
            logger.exception("Unable to persist chat request log")


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
