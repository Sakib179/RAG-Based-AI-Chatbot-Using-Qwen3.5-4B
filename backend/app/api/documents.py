"""Authenticated document upload and indexing endpoint."""

from pathlib import Path
import logging
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.database.repository import create_document
from app.services.auth.auth_dependency import get_current_user
from app.services.auth.auth_service import AuthenticatedUser
from app.services.ingestion.document_loader import SUPPORTED_EXTENSIONS
from app.services.ingestion.processor import IndexResult, process_document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])
KNOWLEDGE_BASE_DIRECTORY = Path(__file__).resolve().parents[3] / "knowledge_base"


class DocumentIndexResponse(BaseModel):
    filename: str
    chunks_indexed: int
    source: str
    document_id: str | None = None


def _safe_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="A filename is required.")
    normalized = filename.replace("\\", "/")
    safe_name = Path(normalized).name
    if not safe_name or safe_name in {".", ".."}:
        raise HTTPException(status_code=400, detail="A valid filename is required.")
    return safe_name


@router.post(
    "/index",
    response_model=DocumentIndexResponse,
    summary="Index a knowledge-base document",
    description="Store, extract, chunk, embed, and persist a supported document for the authenticated user.",
)
async def index_document(
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DocumentIndexResponse:
    filename = _safe_filename(file.filename)
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported document type. Supported extensions: {supported}",
        )

    KNOWLEDGE_BASE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    destination = KNOWLEDGE_BASE_DIRECTORY / filename
    try:
        with destination.open("wb") as output:
            shutil.copyfileobj(file.file, output)
        result: IndexResult = await run_in_threadpool(process_document, destination)
        metadata = await run_in_threadpool(
            create_document, filename, extension.lstrip("."), current_user.id
        )
    except (ValueError, FileNotFoundError) as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        destination.unlink(missing_ok=True)
        logger.exception("Failed to index uploaded document %s", filename)
        raise HTTPException(
            status_code=503,
            detail="The document indexing service is unavailable.",
        ) from exc
    finally:
        await file.close()

    return DocumentIndexResponse(
        filename=filename,
        chunks_indexed=result.chunks_indexed,
        source=filename,
        document_id=str(metadata.get("id")) if metadata.get("id") else None,
    )
