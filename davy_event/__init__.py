"""DAVYLAB Event Radar core."""

from .core import normalize_event, deduplicate_events, verify_event, export_events
from .discovery import discover_events, register_connector, unregister_connector
from .extraction import extract_events
from .ai_extraction import extract_with_model

__all__ = [
    "normalize_event", "deduplicate_events", "verify_event", "export_events",
    "discover_events", "register_connector", "unregister_connector",
    "extract_events", "extract_with_model",
]
__version__ = "0.3.0"
