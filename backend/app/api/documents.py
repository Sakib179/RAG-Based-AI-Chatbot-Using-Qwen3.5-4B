"""Authenticated document upload and indexing endpoint."""

from pathlib import Path
import logging
import shutil

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.services.auth.auth_dependency import get_current_user
from app.services.auth.auth_service import AuthenticatedUser
from app.services.ingestion.document_loader import SUPPORTED_EXTENSIONS
from app.services.ingestion.jobs import create_index_job, get_index_job, run_index_job

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])
KNOWLEDGE_BASE_DIRECTORY = Path(__file__).resolve().parents[3] / "knowledge_base"


class DocumentIndexResponse(BaseModel):
    job_id: str
    status: str
    filename: str
    chunks_indexed: int | None = None
    source: str
    document_id: str | None = None
    message: str | None = None


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
    status_code=status.HTTP_202_ACCEPTED,
    summary="Index a knowledge-base document",
    description="Store, extract, chunk, embed, and persist a supported document for the authenticated user.",
)
async def index_document(
    background_tasks: BackgroundTasks,
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

    job = create_index_job(current_user.id, filename, extension.lstrip("."))
    background_tasks.add_task(run_index_job, job.id, destination)
    return DocumentIndexResponse(
        job_id=job.id,
        status=job.status,
        filename=filename,
        source=filename,
        message="Upload complete. Document indexing is processing in the background.",
    )


@router.get(
    "/index/{job_id}",
    response_model=DocumentIndexResponse,
    summary="Check document indexing status",
    description="Return the status of a background document indexing job owned by the current user.",
)
async def index_status(
    job_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DocumentIndexResponse:
    job = get_index_job(job_id, current_user.id)
    if job is None:
        raise HTTPException(status_code=404, detail="Indexing job not found.")
    return DocumentIndexResponse(
        job_id=job.id,
        status=job.status,
        filename=job.filename,
        chunks_indexed=job.chunks_indexed,
        source=job.filename,
        document_id=job.document_id,
        message=job.error or ("Document indexed successfully." if job.status == "completed" else None),
    )
