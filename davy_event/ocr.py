"""Optional local OCR adapter. Requires Pillow, pytesseract, and Tesseract binary."""
from __future__ import annotations

from io import BytesIO
from typing import Any
import re
import shutil


class OCRUnavailableError(RuntimeError):
    pass


def extract_text_from_image(image_bytes: bytes, *, language: str = "eng", max_bytes: int = 8_000_000) -> dict[str, Any]:
    if not image_bytes or len(image_bytes) > max_bytes:
        raise ValueError("Image is empty or exceeds the configured size limit.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_+.-]{0,39}", language):
        raise ValueError("Invalid OCR language code.")
    try:
        from PIL import Image
        import pytesseract
    except ImportError as exc:
        raise OCRUnavailableError("Install the optional OCR dependencies: pip install -e '.[ocr]'.") from exc
    try:
        image = Image.open(BytesIO(image_bytes))
        image.verify()
        image = Image.open(BytesIO(image_bytes))
        if image.format not in {"PNG", "JPEG", "WEBP", "TIFF"}:
            raise ValueError("Supported image formats: PNG, JPEG, WEBP, TIFF.")
        if image.width * image.height > 24_000_000:
            raise ValueError("Image dimensions exceed the OCR safety limit.")
        text = pytesseract.image_to_string(image, lang=language)
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRUnavailableError("Tesseract OCR binary is not installed on this host.") from exc
    return {"text": text.strip(), "engine": "tesseract", "language": language, "image_format": image.format}


def ocr_status() -> str:
    """Report whether the optional Python packages and Tesseract binary exist."""
    if not shutil.which("tesseract"):
        return "unavailable"
    try:
        import PIL  # noqa: F401
        import pytesseract  # noqa: F401
    except ImportError:
        return "unavailable"
    return "available"
