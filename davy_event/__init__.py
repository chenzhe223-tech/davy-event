"""DAVYLAB Event Radar core."""

from .core import normalize_event, deduplicate_events, verify_event, export_events
from .discovery import discover_events, register_connector, unregister_connector
from .extraction import extract_events

__all__ = [
    "normalize_event", "deduplicate_events", "verify_event", "export_events",
    "discover_events", "register_connector", "unregister_connector", "extract_events",
]
__version__ = "0.3.0"
