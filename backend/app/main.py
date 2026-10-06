"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
from time import perf_counter

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.middleware.exceptions import register_exception_handlers
from app.services.ai.embedding_service import embedding_dependency_available, get_embedding_model

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Configure infrastructure and log application lifecycle events."""

    configure_logging()
    logger.info("Application started")
    if embedding_dependency_available():
        try:
            warmup_started = perf_counter()
            await run_in_threadpool(get_embedding_model)
            logger.info("BGE-M3 embedding model warmed up in %.2fs", perf_counter() - warmup_started)
        except Exception:
            logger.warning("BGE-M3 warmup failed; it will retry on the first chat request", exc_info=True)
    yield
    logger.info("Application stopped")


app = FastAPI(
    title=settings.app_name,
    version="0.4.0",
    description=(
        "AI Knowledge Chatbot backend with local Ollama generation, BGE-M3 "
        "embeddings, ChromaDB retrieval, and document indexing."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
register_exception_handlers(app)
