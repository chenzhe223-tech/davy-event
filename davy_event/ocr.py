"""Optional local OCR adapter. Requires Pillow, pytesseract, and Tesseract binary."""
from __future__ import annotations

from io import BytesIO
from typing import Any
import re
import shutil


class OCRUnavailableError(RuntimeError):
    pass


def extract_text_from_image(
    image_bytes: bytes,
    *,
    language: str = "chi_sim+eng",
    max_bytes: int = 8_000_000,
) -> dict[str, Any]:
    if not image_bytes or len(image_bytes) > max_bytes:
        raise ValueError("Image is empty or exceeds the configured size limit.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_+.-]{0,39}", language):
        raise ValueError("Invalid OCR language code.")
    try:
        from PIL import Image, ImageEnhance, ImageOps
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

        # Poster text is often small and placed over gradients/photos. Upscale and
        # normalize contrast before recognition; keep the original image untouched.
        image = ImageOps.exif_transpose(image).convert("RGB")
        scale = 2 if max(image.size) < 2400 else 1
        if scale > 1:
            image = image.resize((image.width * scale, image.height * scale), Image.Resampling.LANCZOS)
        gray = ImageOps.grayscale(image)
        gray = ImageOps.autocontrast(gray, cutoff=1)
        processed = ImageEnhance.Contrast(gray).enhance(1.25)
        text = pytesseract.image_to_string(
            processed,
            lang=language,
            config="--oem 3 --psm 11",
        )
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRUnavailableError("Tesseract OCR binary is not installed on this host.") from exc
    except pytesseract.TesseractError as exc:
        message = str(exc)
        if "Failed loading language" in message or "Error opening data file" in message:
            raise OCRUnavailableError(
                f"OCR language data is unavailable for '{language}'. Check installed Tesseract language packs."
            ) from exc
        raise
    return {"text": text.strip(), "engine": "tesseract", "language": language, "image_format": image.format}


def ocr_status() -> str:
    """Report whether the optional Python packages and Tesseract binary exist."""
    if not shutil.which("tesseract"):
        return "unavailable"
    try:
        import PIL  # noqa: F401
        import pytesseract
        languages = set(pytesseract.get_languages(config=""))
        if not {"eng", "chi_sim"}.issubset(languages):
            return "partial"
    except (ImportError, Exception):
        return "unavailable"
    return "available"
