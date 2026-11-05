"""Connector interfaces and built-in provider integrations."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ConnectorResult:
    platform: str
    status: str
    records: list[dict[str, Any]]
    message: str | None = None


class EventConnector(Protocol):
    name: str

    def is_available(self) -> bool: ...

    def search(self, query: str, location: str | None = None,
               date_range: dict[str, str] | None = None) -> ConnectorResult: ...


def unavailable(platform: str, reason: str = "No compliant connector is configured.") -> ConnectorResult:
    """Return an honest coverage result; never simulate a platform search."""
    return ConnectorResult(platform=platform, status="unavailable", records=[], message=reason)


from .brave import BraveSearchConnector

__all__ = ["ConnectorResult", "EventConnector", "unavailable", "BraveSearchConnector"]
