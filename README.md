# DAVYLAB Event Radar

A reusable Agent Skill and toolkit for discovering, extracting, validating, deduplicating, and exporting public event information.

Repository: https://github.com/chenzhe223-tech/davy-event

## Use it now

Install local processing:

    git clone https://github.com/chenzhe223-tech/davy-event.git
    cd davy-event
    python -m pip install -e .
    davy-event extract event.html --source-url "https://example.com/event"

## Enable web discovery and REST API

    python -m pip install -e ".[api]"
    export BRAVE_SEARCH_API_KEY="your-key"
    uvicorn davy_event.api:app --host 127.0.0.1 --port 8000

The Brave Search connector uses the official API and keeps the API key server-side. Without a key, coverage is explicitly unavailable.

## Enable poster OCR

Install the Python extra and the Tesseract system binary:

    python -m pip install -e ".[ocr]"

Then install Tesseract and the language packs required by your OS. The API exposes `POST /ocr`.

## API capabilities

- `GET /health`, `GET /connectors` — health and provider readiness.
- `POST /discover` — configured provider search, source coverage, and safe primary-page enrichment (up to five results by default).
- `POST /fetch` — SSRF-resistant public HTTP(S) fetch and event extraction.
- `POST /extract` — supplied HTML, JSON-LD, or text extraction.
- `POST /ocr` — image OCR when the optional engine is installed.
- `POST /normalize`, `/verify`, `/deduplicate`, `/export`.

See [SKILL.md](SKILL.md), [docs/CONNECTORS.md](docs/CONNECTORS.md), and [docs/INTEGRATION.md](docs/INTEGRATION.md).

## Important limits

- Brave Search requires a user-provided API key and may incur provider charges.
- Xiaohongshu, Douyin, and Dianping do not yet have bundled live connectors.
- OCR requires the host's Tesseract binary and language data.
- The REST API should be kept behind authentication and network controls before remote exposure.
- Search snippets and OCR output are candidate evidence, not independently verified event facts.

## License

MIT. See [LICENSE](LICENSE).
