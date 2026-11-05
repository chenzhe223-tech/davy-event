# Changelog

## 0.3.0 — Content extraction
- Added deterministic extraction from Schema.org Event JSON-LD, HTML metadata, and plain text.
- Added MCP `extract_event` tool and public Python API.
- Added extraction tests and documented host-side URL fetching/OCR boundaries.
- No live social-platform connectors are claimed.

## 0.2.0 — Discovery orchestration
- Added provider-agnostic discovery coordinator and runtime connector registry.
- Added source coverage reporting and per-provider error isolation.
- Added MCP discovery tool and connector plugin loading.
- Added mock-provider tests.

## 0.1.0 — Foundation
- Added Agent Skill instructions and compliance boundaries.
- Added normalized event schema.
- Added Python normalization, conservative deduplication, verification checks, and JSON/JSONL export.
- Added connector and integration documentation plus unit tests.
- Platform-specific live connectors remain gated on compliant access methods.
