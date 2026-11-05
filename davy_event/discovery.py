"""Provider-agnostic event discovery orchestration.

No network access is performed here. Applications register connectors that use
official, authorized, or otherwise permitted data sources.
"""
from __future__ import annotations

from typing import Any, Iterable

from .connectors import ConnectorResult, EventConnector, unavailable
from .core import deduplicate_events, normalize_event


def discover_events(
    query: str,
    connectors: Iterable[EventConnector] = (),
    *,
    location: str | None = None,
    date_range: dict[str, str] | None = None,
    platforms: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Search configured connectors and return records plus honest coverage.

    Connector exceptions are isolated so one unavailable provider does not
    suppress results from other providers.
    """
    requested = list(platforms or [])
    providers = list(connectors)
    if not providers:
        coverage = [unavailable(name) for name in (requested or ["all"])]
        return {
            "query": query,
            "status": "unavailable",
            "events": [],
            "coverage": [_coverage(item) for item in coverage],
            "message": "No compliant event connectors are configured.",
        }

    coverage: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for connector in providers:
        if requested and connector.name not in requested:
            continue
        try:
            if not connector.is_available():
                result = unavailable(connector.name)
            else:
                result = connector.search(query, location, date_range)
            coverage.append(_coverage(result))
            for raw in result.records:
                event = normalize_event(raw, result.platform)
                if event.get("source_url") and not event.get("evidence"):
                    event["evidence"] = [{
                        "url": event["source_url"],
                        "source_platform": result.platform,
                        "evidence_type": "connector_record",
                    }]
                events.append(event)
        except Exception as exc:  # provider failures must not break other providers
            coverage.append({
                "platform": connector.name,
                "status": "error",
                "records_count": 0,
                "message": f"Connector failed: {type(exc).__name__}",
            })

    merged = deduplicate_events(events)
    status = "ok" if merged else ("partial" if any(x["status"] == "error" for x in coverage) else "empty")
    return {
        "query": query,
        "status": status,
        "events": merged,
        "coverage": coverage,
        "message": None if merged else "No event records were returned by configured connectors.",
    }


def _coverage(result: ConnectorResult) -> dict[str, Any]:
    return {
        "platform": result.platform,
        "status": result.status,
        "records_count": len(result.records),
        "message": result.message,
    }
