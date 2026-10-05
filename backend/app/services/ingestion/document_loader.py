"""Document and web-page text extraction."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.services.ingestion.ocr import extract_text_from_image


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".docx",
    ".html",
    ".htm",
    ".png",
    ".jpg",
    ".jpeg",
}


@dataclass(frozen=True)
class LoadedDocument:
    """Extracted text with source metadata preserved for retrieval."""

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _metadata(
    source: str,
    filename: str,
    document_type: str,
    page_number: int | None = None,
) -> dict[str, Any]:
    values: dict[str, Any] = {
        "source": source,
        "filename": filename,
        "document_type": document_type,
    }
    if page_number is not None:
        values["page_number"] = page_number
    return values


def _clean_text(text: str) -> str:
    """Normalize extracted text while preserving paragraph boundaries."""

    return "\n".join(line.strip() for line in text.splitlines() if line.strip()).strip()


def _load_pdf(path: Path) -> list[LoadedDocument]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depends on installation
        raise RuntimeError("pypdf is required for PDF ingestion.") from exc

    reader = PdfReader(str(path))
    documents: list[LoadedDocument] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = _clean_text(page.extract_text() or "")
        if text:
            documents.append(
                LoadedDocument(
                    text=text,
                    metadata=_metadata(
                        source=str(path),
                        filename=path.name,
                        document_type="pdf",
                        page_number=page_number,
                    ),
                )
            )
    return documents


def _load_docx(path: Path) -> list[LoadedDocument]:
    try:
        from docx import Document
    except ImportError as exc:  # pragma: no cover - depends on installation
        raise RuntimeError("python-docx is required for DOCX ingestion.") from exc

    document = Document(str(path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    text = _clean_text("\n".join(paragraphs))
    if not text:
        return []
    return [
        LoadedDocument(
            text=text,
            metadata=_metadata(str(path), path.name, "docx"),
        )
    ]


def _extract_html_text(html: str) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover - depends on installation
        raise RuntimeError("beautifulsoup4 is required for HTML ingestion.") from exc

    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    return _clean_text(soup.get_text("\n"))


def _load_html(path: Path) -> list[LoadedDocument]:
    text = _extract_html_text(path.read_text(encoding="utf-8", errors="replace"))
    if not text:
        return []
    return [LoadedDocument(text, _metadata(str(path), path.name, "html"))]


def load_web_page(url: str) -> list[LoadedDocument]:
    """Download a web page and extract readable text from its HTML."""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Web sources must be valid HTTP or HTTPS URLs.")

    try:
        import requests
    except ImportError as exc:  # pragma: no cover - depends on installation
        raise RuntimeError("requests is required for web ingestion.") from exc

    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "AI-Knowledge-Chatbot/1.0"},
    )
    response.raise_for_status()
    text = _extract_html_text(response.text)
    if not text:
        return []
    filename = parsed.path.rsplit("/", maxsplit=1)[-1] or parsed.netloc
    return [LoadedDocument(text, _metadata(url, filename, "web"))]


def load_document(source: str | Path) -> list[LoadedDocument]:
    """Load a local supported document or an HTTP(S) web page."""

    source_text = str(source)
    if source_text.startswith(("http://", "https://")):
        return load_web_page(source_text)

    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"Document not found: {path}")

    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported document type. Supported extensions: {supported}")

    if extension == ".pdf":
        return _load_pdf(path)
    if extension == ".docx":
        return _load_docx(path)
    if extension in {".html", ".htm"}:
        return _load_html(path)
    if extension in {".png", ".jpg", ".jpeg"}:
        text = extract_text_from_image(path)
        return [
            LoadedDocument(
                text=text,
                metadata=_metadata(str(path), path.name, "image"),
            )
        ] if text else []

    text = _clean_text(path.read_text(encoding="utf-8", errors="replace"))
    return [LoadedDocument(text, _metadata(str(path), path.name, "txt"))] if text else []
