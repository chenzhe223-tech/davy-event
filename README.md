# DAVYLAB Event Radar

A reusable, open-source Agent Skill for discovering, extracting, validating, deduplicating, and exporting public event information across social platforms and the open web.

**Repository:** https://github.com/chenzhe223-tech/davy-event

## What it does

- Turns search results, public URLs, and user-provided content into normalized event records.
- Supports pluggable source connectors for Xiaohongshu, Douyin, Dianping, and web search.
- Extracts event title, time, venue, location, price, organizer, registration details, source URL, and evidence.
- Deduplicates cross-platform mentions and flags uncertain or expired information.
- Exposes a stable JSON schema for other apps and agents.

## Important platform boundary

This project does not bypass login, CAPTCHAs, access controls, rate limits, private content, or platform anti-bot protections. Platform connectors must use permitted public access, official/authorized APIs, user-provided exports, or browser sessions explicitly authorized by the user. A connector may return `unsupported` when compliant access is unavailable. Never invent event details.

## Quick start

The first release is an Agent Skill specification and a lightweight Python core.

```bash
pip install -e ".[dev,mcp]"
pytest
```

See [SKILL.md](SKILL.md), [docs/CONNECTORS.md](docs/CONNECTORS.md), and [docs/INTEGRATION.md](docs/INTEGRATION.md).

## Project status

**v0.1.0 — foundation**. Stable event schema, source contract, extraction/verification guidance, and starter Python package. Live platform integrations are deliberately gated on a compliant access method and credentials where required.

## License

MIT. See [LICENSE](LICENSE).
