# Integration guide

## Python

```python
from davy_event import normalize_event, deduplicate_events, verify_event, export_events

event = normalize_event({
    "活动名称": "Weekend Family Workshop",
    "开始时间": "2026-11-07T10:00:00+08:00",
    "地址": "Singapore",
    "原文链接": "https://example.org/event"
}, source="web")

events = deduplicate_events([event])
events = [verify_event(item) for item in events]
print(export_events(events))
```

## Agent Skill

Install or reference this repository as a Skill and follow the root `SKILL.md`. An agent should call only connectors configured in its runtime and must disclose source coverage.

## MCP / HTTP adapters

The `adapters/mcp` directory is reserved for a transport adapter. The core event schema is transport-neutral; consumers may wrap it in MCP tools, REST endpoints, or direct Python calls without changing the schema.

## Suggested tool names

- `discover_events`
- `extract_event`
- `verify_event`
- `deduplicate_events`
- `search_nearby_events`
- `export_events`

Input and output should use `schemas/event.schema.json`.
