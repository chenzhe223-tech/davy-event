# DAVYLAB Event Radar — Windows PowerShell quick start
# Run this script from the repository root.

$ErrorActionPreference = "Stop"

python --version
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.10+ is required. Install Python and retry."
}

python -m pip install --upgrade pip
python -m pip install -e ".[api,mcp]"

# Optional: configure Brave Search API access on this machine.
# Obtain a key from https://brave.com/search/api/ and set it locally:
# $env:BRAVE_SEARCH_API_KEY = "your-key"

# Recommended even for local use; required if you later expose the API.
# $env:DAVY_EVENT_API_TOKEN = "your-long-random-token"

Write-Host ""
Write-Host "Local API will start on http://127.0.0.1:8000"
Write-Host "Swagger docs: http://127.0.0.1:8000/docs"
Write-Host "Connector status: http://127.0.0.1:8000/connectors"
Write-Host "Press Ctrl+C to stop."
python -m uvicorn davy_event.api:app --host 127.0.0.1 --port 8000
