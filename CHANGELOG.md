# Changelog

## 0.4.0 — Usable local workflow

- Expanded SKILL.md with task triggers, honest source coverage, installation, CLI, and MCP usage.
- Added davy-event CLI for extracting, normalizing, verifying, deduplicating, and exporting local event data.
- Added tests for CLI extraction, validation errors, and JSONL export.
- Local processing requires no API key. Live discovery still requires a separately configured compliant connector.

## 0.3.0 — Content extraction

- Added deterministic extraction from Schema.org Event JSON-LD, HTML metadata, and supplied text.
- Added optional host-provided LLM extraction with verbatim source-quote grounding.
- Added MCP extraction tool and expanded documentation.

## 0.2.0 — Discovery orchestration

- Added provider-agnostic discovery orchestration, connector registry, coverage reporting, and MCP discovery tool.

## 0.1.0 — Core

- Added event normalization, conservative deduplication, verification labels, JSON/JSONL export, connector contract, and MCP adapter.
