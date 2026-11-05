# Changelog

## 0.5.0 — Search, safe fetch, OCR and REST API foundation

- Added Brave Search API connector with server-side token configuration and honest unavailable status.
- Added SSRF-resistant public HTTP(S) fetcher with pinned DNS resolution, redirect revalidation, content-type and response-size limits.
- Added optional Tesseract OCR adapter for supplied event posters.
- Added FastAPI endpoints for health, connector readiness, discovery, fetch, extraction, OCR, normalization, verification, deduplication, and export.
- Connected search results to safe primary-page retrieval and event extraction (bounded to at most ten pages per request).
- Added connector, fetcher, and API tests; CI installs and tests API dependencies.
- Social platforms remain unavailable until separately authorized connectors are implemented.

## 0.4.0 — Usable local workflow

- Expanded SKILL.md with task triggers, honest source coverage, installation, CLI, and MCP usage.
- Added davy-event CLI for extracting, normalizing, verifying, deduplicating, and exporting local event data.

## 0.3.0 — Content extraction

- Added deterministic extraction from Schema.org Event JSON-LD, HTML metadata, and supplied text.
- Added optional host-provided LLM extraction with verbatim source-quote grounding.
- Added MCP extraction tool and expanded documentation.

## 0.2.0 — Discovery orchestration

- Added provider-agnostic discovery orchestration, connector registry, coverage reporting, and MCP discovery tool.

## 0.1.0 — Core

- Added event normalization, conservative deduplication, verification labels, JSON/JSONL export, connector contract, and MCP adapter.
