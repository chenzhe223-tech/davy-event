# DAVYLAB Event Radar

A reusable Agent Skill and Python toolkit for discovering, extracting, validating, deduplicating, and exporting public event information.

Repository: https://github.com/chenzhe223-tech/davy-event

## Quick start

    git clone https://github.com/chenzhe223-tech/davy-event.git
    cd davy-event
    python -m pip install -e .

Process supplied content locally without API keys:

    davy-event extract event.html --source-url "https://example.com/event"
    davy-event normalize event.json
    davy-event verify event.json
    davy-event dedupe events.json
    davy-event export events.json --format jsonl

Run the MCP server for compatible AI clients:

    python -m pip install -e ".[mcp]"
    python -m davy_event.adapters.mcp.server

See SKILL.md for the complete agent workflow and docs/CONNECTORS.md for provider integration.

## Capabilities and limits

- Extracts event candidates from supplied HTML, Schema.org Event JSON-LD, structured records, and plain text.
- Offers optional host-provided LLM extraction with verbatim source-quote checks.
- Normalizes records, preserves evidence, deduplicates, checks completeness, and exports JSON/JSONL.
- Provides a pluggable connector contract, discovery orchestration, coverage reporting, and MCP tools.
- No live Xiaohongshu, Douyin, Dianping, or general web search connector is bundled yet.
- The core does not fetch URLs. The host application must safely retrieve public page content or accept user-supplied content.

## Project status

v0.4.0: usable local workflow. Local processing is available without API keys. Live discovery requires separately configured, compliant connectors. See CHANGELOG.md.

## License

MIT. See LICENSE.
