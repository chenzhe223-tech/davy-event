import pytest
from davy_event.ocr import extract_text_from_image, ocr_status


def test_ocr_rejects_invalid_language_code_before_loading_engine():
    with pytest.raises(ValueError, match="language"):
        extract_text_from_image(b"not-an-image", language="--version")


def test_ocr_status_is_explicit():
    assert ocr_status() in {"available", "unavailable"}
