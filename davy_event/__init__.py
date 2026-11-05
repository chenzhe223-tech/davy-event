"""DAVYLAB Event Radar core."""

from .core import normalize_event, deduplicate_events, verify_event, export_events
from .discovery import discover_events

__all__ = ["normalize_event", "deduplicate_events", "verify_event", "export_events", "discover_events"]
__version__ = "0.2.0"
