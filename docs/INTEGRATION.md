# Integration guide

## Local CLI

Install and use the local CLI without an API key:

    pip install -e .
    davy-event extract event.html --source-url "https://example.org/event"

## Brave web discovery

Set `BRAVE_SEARCH_API_KEY` on the server. The built-in `web-search` connector returns public search candidates with provenance. Search snippets are not independently verified event facts.

## REST API

Install and run:

    pip install -e ".[api]"
    uvicorn davy_event.api:app --host 127.0.0.1 --port 8000

The default bind is loopback in this example. Put the service behind authenticated access and TLS before exposing it to a network. Configure the Brave key as a server environment variable.

Endpoints:
- `GET /health`
- `POST /discover` — query configured providers and return source coverage.
- `POST /extract` — extract events from supplied text, HTML, or JSON-LD.
- `POST /fetch` — safely fetch public HTTP(S) pages and extract event candidates.
- `POST /ocr` — OCR a supplied image when optional OCR dependencies and the Tesseract binary are installed.
- `POST /normalize`
- `POST /verify`
- `POST /deduplicate`
- `POST /export`

The fetcher permits only HTTP/HTTPS on standard ports, rejects credentials and non-public DNS answers, pins the validated destination IP for the connection, manually validates each redirect, restricts content types, and limits response bytes and time. It is not a substitute for an outbound firewall or service isolation.

## URL fetching security

The fetcher uses direct pinned-IP connections to avoid a second DNS lookup after validation. It rejects a hostname if any resolved address is non-global, preventing mixed public/private DNS answers from being accepted. Redirect targets are independently resolved and validated. Only HTML, XHTML, plain text, and JSON-LD are accepted.

Security reference: OWASP SSRF Prevention Cheat Sheet.

## OCR

Install Python dependencies:

    pip install -e ".[ocr]"

The host must also install the Tesseract OCR binary and required language data. Example:

    sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim
    curl -F "file=@poster.jpg" "http://127.0.0.1:8000/ocr?language=chi_sim+eng"

OCR output is source-derived text, not verified fact. Event candidates extracted from OCR remain source claims.

## MCP server

Install and start:

    pip install -e ".[mcp]"
    python -m davy_event.adapters.mcp.server

MCP exposes extraction, discovery, normalization, verification, deduplication, export, and connector status. Authorized connector plugins may be loaded through `DAVY_EVENT_CONNECTOR_MODULES`.
