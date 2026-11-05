"""Optional FastAPI service for DAVYLAB Event Radar."""
from __future__ import annotations

import os
import http.client
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .ai_extraction import extract_with_model
from .connectors.brave import BraveSearchConnector
from .core import deduplicate_events, export_events, normalize_event, verify_event
from .discovery import discover_events as run_discovery, register_connector, connector_status as get_connector_status, registered_connector_names
from .extraction import extract_events
from .fetcher import UnsafeURLError, fetch_public_url
from .ocr import OCRUnavailableError, extract_text_from_image


class ExtractRequest(BaseModel):
    content: str | dict[str, Any] | list[Any]
    source_url: str | None = None
    source_platform: str = "user-provided"


class DiscoverRequest(BaseModel):
    query: str = Field(min_length=1, max_length=600)
    location: str | None = None
    date_range: dict[str, str] | None = None
    platforms: list[str] | None = None
    fetch_sources: bool = True
    max_sources: int = Field(default=5, ge=0, le=10)


class NormalizeRequest(BaseModel):
    event: dict[str, Any]
    source_platform: str = "unknown"


class VerifyRequest(BaseModel):
    event: dict[str, Any]
    evidence: list[dict[str, Any]] | None = None


class EventsRequest(BaseModel):
    events: list[dict[str, Any]]
    format: str = "json"


class FetchRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)


def create_app() -> FastAPI:
    app = FastAPI(
        title="DAVYLAB Event Radar API",
        version="0.5.0",
        description="Compliant event discovery, extraction, URL fetching, OCR, verification and export.",
    )
    # Registered even without a key so coverage explicitly reports unavailable.
    register_connector(BraveSearchConnector())

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": "0.5.0",
            "connectors": {"web-search": "configured" if os.getenv("BRAVE_SEARCH_API_KEY") else "unavailable"},
            "ocr": "optional",
        }

    @app.get("/connectors")
    def connectors() -> dict[str, Any]:
        known = set(registered_connector_names()) | {"web-search", "xiaohongshu", "douyin", "dianping"}
        return {"connectors": [get_connector_status(name) for name in sorted(known)]}

    @app.post("/extract")
    def extract(request: ExtractRequest) -> dict[str, Any]:
        return {"events": extract_events(request.content, source_url=request.source_url, source_platform=request.source_platform)}

    @app.post("/discover")
    def discover(request: DiscoverRequest) -> dict[str, Any]:
        result = run_discovery(
            request.query,
            location=request.location,
            date_range=request.date_range,
            platforms=request.platforms,
        )
        if request.fetch_sources and result.get("events"):
            for candidate in result["events"][:request.max_sources]:
                source_url = candidate.get("source_url")
                if not source_url:
                    candidate["fetch_status"] = "no_source_url"
                    continue
                try:
                    page = fetch_public_url(source_url)
                    extracted = extract_events(
                        page.text, source_url=page.final_url, source_platform="web"
                    )
                    candidate["fetch_status"] = "fetched"
                    candidate["fetched_url"] = page.final_url
                    candidate["evidence"] = list(candidate.get("evidence") or []) + [{
                        "type": "fetched_page",
                        "source_url": page.final_url,
                        "content_type": page.content_type,
                        "byte_count": page.byte_count,
                    }]
                    if extracted:
                        detail = extracted[0]
                        for key, value in detail.items():
                            if value not in (None, "", []):
                                if key == "title" and candidate.get("title"):
                                    continue
                                candidate[key] = value
                        candidate["verification_status"] = "source_claim"
                except UnsafeURLError as exc:
                    candidate["fetch_status"] = "blocked"
                    candidate["fetch_message"] = str(exc)
                except (RuntimeError, OSError, http.client.HTTPException) as exc:
                    candidate["fetch_status"] = "fetch_error"
                    candidate["fetch_message"] = str(exc)
        result["enrichment"] = {
            "enabled": request.fetch_sources,
            "max_sources": request.max_sources,
            "description": "Search candidates are enriched from safely fetched public pages; they remain source claims until corroborated."
        }
        return result

    @app.post("/normalize")
    def normalize(request: NormalizeRequest) -> dict[str, Any]:
        return normalize_event(request.event, request.source_platform)

    @app.post("/verify")
    def verify(request: VerifyRequest) -> dict[str, Any]:
        return verify_event(request.event, request.evidence)

    @app.post("/deduplicate")
    def deduplicate(request: EventsRequest) -> dict[str, Any]:
        return {"events": deduplicate_events(request.events)}

    @app.post("/export")
    def export(request: EventsRequest) -> dict[str, str]:
        if request.format not in {"json", "jsonl"}:
            raise HTTPException(status_code=400, detail="format must be json or jsonl")
        return {"content": export_events(request.events, request.format), "format": request.format}

    @app.post("/fetch")
    def fetch(request: FetchRequest) -> dict[str, Any]:
        try:
            page = fetch_public_url(request.url)
        except UnsafeURLError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except (RuntimeError, OSError, http.client.HTTPException) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        events = extract_events(page.text, source_url=page.final_url, source_platform="web")
        return {
            "requested_url": page.requested_url,
            "final_url": page.final_url,
            "status_code": page.status_code,
            "content_type": page.content_type,
            "byte_count": page.byte_count,
            "events": events,
        }

    @app.post("/ocr")
    async def ocr(file: UploadFile = File(...), language: str = "eng") -> dict[str, Any]:
        data = await file.read(8_000_001)
        if len(data) > 8_000_000:
            raise HTTPException(status_code=413, detail="Image exceeds 8 MB.")
        try:
            result = extract_text_from_image(data, language=language)
        except OCRUnavailableError as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {**result, "events": extract_events(result["text"], source_platform="image-ocr")}

    return app


app = create_app()
