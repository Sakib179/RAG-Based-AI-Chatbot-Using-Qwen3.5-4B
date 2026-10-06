"""In-process indexing jobs for responsive document uploads.

The uploaded file is returned to the client before CPU-heavy embedding starts.
Jobs are intentionally small and process-local for this single-worker setup;
the vector data itself remains durable in ChromaDB.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Literal
from uuid import UUID, uuid4
import logging

from app.database.repository import create_document
from app.services.ingestion.processor import IndexResult, process_document

logger = logging.getLogger(__name__)
JobStatus = Literal["pending", "processing", "completed", "failed"]


@dataclass
class IndexJob:
    id: str
    user_id: str
    filename: str
    file_type: str
    status: JobStatus = "pending"
    chunks_indexed: int | None = None
    document_id: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


_jobs: dict[str, IndexJob] = {}
_jobs_lock = Lock()


def create_index_job(user_id: UUID | str, filename: str, file_type: str) -> IndexJob:
    job = IndexJob(id=str(uuid4()), user_id=str(user_id), filename=filename, file_type=file_type)
    with _jobs_lock:
        _jobs[job.id] = job
    return job


def get_index_job(job_id: str, user_id: UUID | str) -> IndexJob | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None or job.user_id != str(user_id):
            return None
        return job


def _set_job(job: IndexJob, **changes: object) -> None:
    with _jobs_lock:
        for name, value in changes.items():
            setattr(job, name, value)
        job.updated_at = datetime.now(timezone.utc)


def run_index_job(job_id: str, path: str | Path) -> None:
    """Run extraction and embedding after the upload response is returned."""

    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        logger.error("Index job %s disappeared before processing", job_id)
        return

    _set_job(job, status="processing")
    try:
        result: IndexResult = process_document(path)
        metadata = create_document(job.filename, job.file_type, job.user_id)
        _set_job(
            job,
            status="completed",
            chunks_indexed=result.chunks_indexed,
            document_id=str(metadata.get("id")) if metadata.get("id") else None,
        )
        logger.info("Index job %s completed: %s chunks", job_id, result.chunks_indexed)
    except Exception:
        logger.exception("Index job %s failed for %s", job_id, job.filename)
        _set_job(
            job,
            status="failed",
            error="Document processing failed. Check backend logs for details.",
        )
