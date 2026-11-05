# DAVYLAB Event Radar

A reusable, open-source Agent Skill and Python core for discovering, extracting, validating, deduplicating, and exporting public event information.

**Repository:** https://github.com/chenzhe223-tech/davy-event

## What it does

- Normalizes event records from authorized providers, public sources, and user-provided content.
- Provides a pluggable connector contract and provider-agnostic discovery orchestration.
- Reports source coverage and provider failures instead of pretending unavailable sources were searched.
- Deduplicates cross-source mentions and preserves provenance/evidence.
- Exposes Python functions, an MCP server, and a stable JSON schema for other apps and agents.

## Platform boundary

Xiaohongshu, Douyin, and Dianping are target integrations, not currently live connectors. They require an official/authorized API, permitted public access, or user-provided exports. This project does not bypass login, CAPTCHAs, access controls, rate limits, private content, or anti-bot protections. Never invent event details.

## Quick start

```bash
pip install -e ".[dev,mcp]"
pytest
```

Start the MCP server:

```bash
python -m davy_event.adapters.mcp.server
```

See [SKILL.md](SKILL.md), [docs/CONNECTORS.md](docs/CONNECTORS.md), and [docs/INTEGRATION.md](docs/INTEGRATION.md).

## Project status

**v0.2.0 — discovery orchestration**. Includes a provider contract, discovery coordinator, source coverage reporting, MCP tools, and mock-provider tests. No live social-platform connector is claimed.

## License

MIT. See [LICENSE](LICENSE).
