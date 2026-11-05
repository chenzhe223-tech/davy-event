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

On Windows, run `examples/quickstart.ps1` from PowerShell for the local API setup. The script binds only to `127.0.0.1` and does not expose the service publicly.

    python -m pip install -e ".[api]"
    $env:VOLCENGINE_SEARCH_API_KEY = "your-key"
    export DAVY_EVENT_API_TOKEN="set-a-long-random-token-for-remote-access"
    uvicorn davy_event.api:app --host 127.0.0.1 --port 8000

The default `web-search` connector uses the official Volcengine Doubao Global Search API. Set `VOLCENGINE_SEARCH_API_KEY` on the server; the key is never sent to browser clients. Each account currently receives 500 free searches per month, shared by Global and Custom editions. When free quota is exhausted, the connector reports an error and does not switch to a paid provider.

## Enable poster OCR

OCR requires both the Python extra and the Tesseract system engine plus language data.

Local Python dependencies:

    python -m pip install -e ".[ocr]"

On Debian 12 / Render native Python runtime, install the system engine and English + Simplified Chinese language data:

    sudo apt-get update
    sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-sim

For a Render deployment that enables the API and OCR together, use this build command:

    sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-sim && python -m pip install --upgrade pip && python -m pip install ".[api,ocr]" && tesseract --version

The API exposes `POST /ocr`. The default language is `eng`; use `chi_sim` for Simplified Chinese or `chi_sim+eng` for mixed Chinese-English posters after installing the corresponding language data.

## API capabilities

- `GET /health`, `GET /connectors` — health and provider readiness.
- `POST /discover` — configured provider search, source coverage, and safe primary-page enrichment (up to five results by default).
- `POST /fetch` — SSRF-resistant public HTTP(S) fetch and event extraction.
- `POST /extract` — supplied HTML, JSON-LD, or text extraction.
- `POST /ocr` — image OCR when the optional engine is installed.
- `POST /normalize`, `/verify`, `/deduplicate`, `/export`.

See [SKILL.md](SKILL.md), [docs/CONNECTORS.md](docs/CONNECTORS.md), and [docs/INTEGRATION.md](docs/INTEGRATION.md).

## Important limits

- Volcengine search requires a user-provided API key. The provider currently documents 500 free searches per account per month; this is a quota, not an unlimited free plan. No automatic paid fallback is configured.
- Xiaohongshu, Douyin, and Dianping do not yet have bundled live connectors.
- OCR requires the host's Tesseract binary and the requested language data.
- Set DAVY_EVENT_API_TOKEN to require Bearer authentication on API routes other than health/docs; keep network controls in place as well.
- Search snippets and OCR output are candidate evidence, not independently verified event facts.

## License

MIT. See [LICENSE](LICENSE).
