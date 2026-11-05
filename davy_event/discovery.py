"""Provider-agnostic event discovery orchestration.

No network access is performed here. Applications register connectors that use
official, authorized, or otherwise permitted data sources.
"""
from __future__ import annotations

from typing import Any, Iterable

from .connectors import ConnectorResult, EventConnector, unavailable
from .core import deduplicate_events, normalize_event


_REGISTERED_CONNECTORS: dict[str, EventConnector] = {}


def register_connector(connector: EventConnector) -> None:
    """Register or replace a provider by its stable name."""
    _REGISTERED_CONNECTORS[connector.name] = connector


def unregister_connector(name: str) -> None:
    """Remove a previously registered provider."""
    _REGISTERED_CONNECTORS.pop(name, None)


def discover_events(
    query: str,
    connectors: Iterable[EventConnector] | None = None,
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
    providers = list(connectors if connectors is not None else _REGISTERED_CONNECTORS.values())
    if requested:
        providers = [provider for provider in providers if provider.name in requested]
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

    covered = {item["platform"] for item in coverage}
    for missing_platform in requested:
        if missing_platform not in covered:
            coverage.append(_coverage(unavailable(missing_platform)))
    merged = deduplicate_events(events)
    status = "ok" if merged else ("partial" if any(x["status"] == "error" for x in coverage) else ("unavailable" if coverage and all(x["status"] == "unavailable" for x in coverage) else "empty"))
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


def connector_status(platform: str) -> dict[str, Any]:
    """Return actual configured provider status without attempting a search."""
    connector = _REGISTERED_CONNECTORS.get(platform)
    if connector is None:
        return {
            "platform": platform,
            "status": "unavailable",
            "message": "No connector is registered for this source.",
        }
    try:
        available = bool(connector.is_available())
    except Exception as exc:
        return {
            "platform": platform,
            "status": "error",
            "message": f"Connector status check failed: {type(exc).__name__}",
        }
    return {
        "platform": platform,
        "status": "available" if available else "unavailable",
        "message": None if available else "Connector is registered but its credentials or access route are not configured.",
    }


def registered_connector_names() -> list[str]:
    """Return stable names of currently registered connectors."""
    return sorted(_REGISTERED_CONNECTORS)
