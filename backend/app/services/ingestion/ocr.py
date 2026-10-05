"""Local OCR support for PNG and JPEG images."""

from pathlib import Path


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def extract_text_from_image(path: str | Path) -> str:
    """Extract text from an image using Pillow and the local Tesseract binary."""

    image_path = Path(path)
    if image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError("OCR supports only PNG, JPG, and JPEG files.")

    try:
        from PIL import Image
        import pytesseract
    except ImportError as exc:  # pragma: no cover - depends on installation
        raise RuntimeError("Pillow and pytesseract are required for OCR.") from exc

    with Image.open(image_path) as image:
        return pytesseract.image_to_string(image).strip()
