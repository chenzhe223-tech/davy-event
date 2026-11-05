# Integration guide

## Python: register a compliant provider

The discovery engine is provider-agnostic. It does not scrape websites or call social platforms by itself. Implement the connector contract using an official API, an authorized data provider, permitted public access, or user-supplied exports.

```python
from davy_event import discover_events
from davy_event.connectors import ConnectorResult

class MyAuthorizedProvider:
    name = "authorized-web"

    def is_available(self):
        return True

    def search(self, query, location=None, date_range=None):
        # Replace with your authorized provider call.
        records = [{
            "title": "Weekend Family Workshop",
            "start_datetime": "2026-11-07T10:00:00+08:00",
            "address": "Singapore",
            "source_url": "https://example.org/event",
        }]
        return ConnectorResult(self.name, "ok", records)

result = discover_events("family workshop", [MyAuthorizedProvider()], location="Singapore")
print(result["status"], result["coverage"], result["events"])
```

The example record illustrates the required shape; it is not a live event listing.

## Process user-provided records

```python
from davy_event import normalize_event, verify_event, deduplicate_events, export_events

event = normalize_event({
    "活动名称": "Weekend Family Workshop",
    "开始时间": "2026-11-07T10:00:00+08:00",
    "地址": "Singapore",
    "原文链接": "https://example.org/event"
}, source="user-provided")

events = deduplicate_events([verify_event(event)])
print(export_events(events, "json"))
```

## Agent Skill

Install or reference this repository as a Skill and follow the root `SKILL.md`. An agent should call only connectors configured in its runtime and must disclose source coverage.

## MCP server

Install and start:

```bash
pip install -e ".[mcp]"
python -m davy_event.adapters.mcp.server
```

The MCP server exposes `discover_events`, `normalize`, `deduplicate`, `verify`, `export`, and `connector_status`. The default server process has no platform connectors registered, so `discover_events` correctly returns `unavailable` until the host application supplies and registers a compliant provider. Core Python integrations can register providers directly.

## Tool contract

- `discover_events`: query, optional platform list, location and date range; returns events, per-source coverage and status.
- `normalize`: convert one source record to the shared schema.
- `verify`: check completeness and evidence metadata; it does not independently browse.
- `deduplicate`: merge conservative exact matches while preserving source URLs.
- `export`: JSON or JSONL.

Input and output should use `schemas/event.schema.json`.
