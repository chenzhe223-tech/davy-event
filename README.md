# DAVYLAB Event Radar

A reusable, open-source Agent Skill and Python core for discovering, extracting, validating, deduplicating, and exporting public event information.

**Repository:** https://github.com/chenzhe223-tech/davy-event

## What it does

- Extracts event candidates from supplied HTML, Schema.org Event JSON-LD, structured records, and plain text.
- Offers an optional host-provided LLM extraction callback with verbatim source-quote checks.
- Normalizes event details and preserves source URLs and evidence.
- Provides a pluggable connector contract and provider-agnostic discovery orchestration.
- Reports source coverage and provider failures instead of pretending unavailable sources were searched.
- Exposes Python functions, an MCP server, and a stable JSON schema for other apps and agents.

## Platform boundary

Xiaohongshu, Douyin, and Dianping are target integrations, not currently live connectors. They require an official/authorized API, permitted public access, or user-provided exports. This project does not bypass login, CAPTCHAs, access controls, rate limits, private content, or anti-bot protections. The extraction module processes content supplied by the host application; it does not crawl or fetch URLs itself.

## Quick start

\`\`\`bash
pip install -e ".[dev,mcp]"
pytest
\`\`\`

Start the MCP server:

\`\`\`bash
python -m davy_event.adapters.mcp.server
\`\`\`

See [SKILL.md](SKILL.md), [docs/CONNECTORS.md](docs/CONNECTORS.md), and [docs/INTEGRATION.md](docs/INTEGRATION.md).

## Project status

**v0.3.0 — content extraction**. Includes provider discovery orchestration, deterministic Schema.org/JSON-LD and text extraction, an optional LLM callback with source-quote grounding, MCP extraction tools, and automated tests. No live social-platform connector is claimed.

## License

MIT. See [LICENSE](LICENSE).
