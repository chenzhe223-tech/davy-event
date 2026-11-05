"""Optional MCP server exposing DAVYLAB Event Radar core utilities.

Install with: pip install -e ".[mcp]"
Run with: python -m davy_event.adapters.mcp.server
"""
from __future__ import annotations

import json
from mcp.server.fastmcp import FastMCP

from davy_event import normalize_event, deduplicate_events, verify_event, export_events
from davy_event.connectors import unavailable

mcp = FastMCP("davy-event")


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
    """Report availability honestly; live platform search needs a configured compliant connector."""
    result = unavailable(platform)
    return {"platform": result.platform, "status": result.status, "message": result.message, "records": result.records}


if __name__ == "__main__":
    mcp.run()
