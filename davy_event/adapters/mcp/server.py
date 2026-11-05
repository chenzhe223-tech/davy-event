"""Optional MCP server exposing DAVYLAB Event Radar tools.

Install with: pip install -e ".[mcp]"
Run with: python -m davy_event.adapters.mcp.server

Optional connector plugins can be loaded from comma-separated module names in
DAVY_EVENT_CONNECTOR_MODULES. Each module may expose register_connectors(),
which returns connector instances or registers them using register_connector().
"""
from __future__ import annotations

import importlib
import os

from mcp.server.fastmcp import FastMCP

from davy_event import (
    normalize_event, deduplicate_events, verify_event, export_events,
    register_connector,
)
from davy_event.extraction import extract_events
from davy_event.connectors import unavailable
from davy_event.discovery import discover_events as run_discovery


def _load_connector_plugins() -> None:
    modules = [name.strip() for name in os.getenv("DAVY_EVENT_CONNECTOR_MODULES", "").split(",") if name.strip()]
    for module_name in modules:
        module = importlib.import_module(module_name)
        factory = getattr(module, "register_connectors", None)
        if callable(factory):
            connectors = factory() or []
            for connector in connectors:
                register_connector(connector)


_load_connector_plugins()
mcp = FastMCP("davy-event")


@mcp.tool()
def discover_events(query: str, platforms: list[str] | None = None,
                    location: str | None = None,
                    date_range: dict | None = None) -> dict:
    """Search configured compliant providers; reports unavailable when none are registered."""
    return run_discovery(query, location=location, date_range=date_range, platforms=platforms)


@mcp.tool()
def extract_event(content: str | dict | list, source_url: str | None = None,
                  source_platform: str = "user-provided") -> list[dict]:
    """Extract event candidates from supplied HTML, JSON-LD, or text. No URL is fetched."""
    return extract_events(content, source_url=source_url, source_platform=source_platform)


@mcp.tool()
def normalize(raw_event: dict, source_platform: str = "unknown") -> dict:
    """Normalize a raw event record to the shared DAVYLAB event structure."""
    return normalize_event(raw_event, source_platform)


@mcp.tool()
def deduplicate(events: list[dict]) -> list[dict]:
    """Conservatively deduplicate event records and retain all source URLs."""
    return deduplicate_events(events)


@mcp.tool()
def verify(event: dict, evidence: list[dict] | None = None) -> dict:
    """Check event completeness and assign a cautious verification label."""
    return verify_event(event, evidence)


@mcp.tool()
def export(events: list[dict], format: str = "json") -> str:
    """Export event records as JSON or JSON Lines."""
    return export_events(events, format)


@mcp.tool()
def connector_status(platform: str) -> dict:
    """Report availability honestly; live search needs a configured compliant connector."""
    result = unavailable(platform)
    return {"platform": result.platform, "status": result.status,
            "message": result.message, "records": result.records}


if __name__ == "__main__":
    mcp.run()
