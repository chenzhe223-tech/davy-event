# Integration guide

## Deterministic extraction

Pass page content already obtained by your host application. The extractor supports Schema.org Event JSON-LD, HTML pages containing JSON-LD, and plain text. It does not fetch URLs or execute scripts.

\`\`\`python
from davy_event import extract_events

events = extract_events(
    html_or_text,
    source_url="https://example.org/event-page",
    source_platform="web",
)
\`\`\`

## Optional LLM extraction

Any host application can supply its own model callback. The extractor requires at least one exact, verbatim source quote for each accepted event and always labels the result as a source claim, not independently verified.

\`\`\`python
from davy_event import extract_with_model

def my_model(system_prompt, source_text):
    # Call your configured model and return a JSON object or JSON string.
    ...

events = extract_with_model(
    source_text,
    my_model,
    source_url="https://example.org/post",
    source_platform="user-provided",
)
\`\`\`

For screenshots, use an OCR or vision model in the host application first, then pass the recognized text to either extractor. OCR-derived fields should remain source claims until checked against the original post or organizer.

## Python: register a compliant provider

The discovery engine is provider-agnostic. It does not scrape websites or call social platforms by itself. Implement the connector contract using an official API, an authorized data provider, permitted public access, or user-supplied exports.

\`\`\`python
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
\`\`\`

The example record illustrates the required shape; it is not a live event listing.

For reusable in-process registration, call \`register_connector(instance)\`; later calls to \`discover_events(query)\` use the registered providers. Use \`unregister_connector(name)\` to remove one.

## Process user-provided records

\`\`\`python
from davy_event import normalize_event, verify_event, deduplicate_events, export_events

event = normalize_event({
    "活动名称": "Weekend Family Workshop",
    "开始时间": "2026-11-07T10:00:00+08:00",
    "地址": "Singapore",
    "原文链接": "https://example.org/event"
}, source="user-provided")

events = deduplicate_events([verify_event(event)])
print(export_events(events, "json"))
\`\`\`

## Agent Skill

Install or reference this repository as a Skill and follow the root \`SKILL.md\`. An agent should call only connectors configured in its runtime and must disclose source coverage.

## MCP server

Install and start:

\`\`\`bash
pip install -e ".[mcp]"
python -m davy_event.adapters.mcp.server
\`\`\`

The MCP server exposes \`discover_events\`, \`extract_event\`, \`normalize\`, \`deduplicate\`, \`verify\`, \`export\`, and \`connector_status\`. By default, discovery returns \`unavailable\` because no live providers are bundled. The extraction tool processes supplied content only; it does not fetch a URL.

To load authorized provider plugins, set \`DAVY_EVENT_CONNECTOR_MODULES\` to a comma-separated list of importable Python module names before starting the server. Each module must expose \`register_connectors()\`, returning connector instances; alternatively, it may register providers itself using \`register_connector(instance)\` during import. Only load trusted local modules.

## Tool contract

- \`discover_events\`: query, optional platform list, location and date range; returns events, per-source coverage and status.
- \`extract_event\`: parse supplied HTML, JSON-LD, dictionaries, or text into event candidates.
- \`normalize\`: convert one source record to the shared schema.
- \`verify\`: check completeness and evidence metadata; it does not independently browse.
- \`deduplicate\`: merge conservative exact matches while preserving source URLs.
- \`export\`: JSON or JSONL.

Input and output should use \`schemas/event.schema.json\`.
