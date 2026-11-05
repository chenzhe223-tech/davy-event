"""Volcengine Doubao Search Global connector (free quota first)."""
from __future__ import annotations

import json
import os
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from davy_event.connectors import ConnectorResult


class VolcengineSearchConnector:
    """Official Volcengine Global Search API; never switches to paid providers."""

    name = "web-search"
    endpoint = "https://open.feedcoopapi.com/search_api/global_search"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        count: int = 10,
        timeout: float = 15.0,
        request_json: Callable[..., dict[str, Any]] | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("VOLCENGINE_SEARCH_API_KEY")
        self.count = max(1, min(int(count), 20))
        self.timeout = timeout
        self._request_json = request_json or self._http_request_json

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _http_request_json(self, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        request = Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read(2_000_001)
        except HTTPError as exc:
            # Do not include request headers or credentials in provider errors.
            try:
                detail = exc.read(16_384).decode("utf-8", errors="replace")
                parsed = json.loads(detail)
                metadata = parsed.get("ResponseMetadata") or {}
                error = metadata.get("Error") or {}
                code = error.get("Code") or error.get("CodeN") or exc.code
                message = error.get("Message") or "request rejected"
            except Exception:
                code, message = exc.code, "request rejected"
            raise RuntimeError(f"Volcengine Search API HTTP {code}: {message}") from exc
        except URLError as exc:
            raise RuntimeError("Volcengine Search API request failed") from exc
        if len(raw) > 2_000_000:
            raise RuntimeError("Volcengine Search API response exceeded the size limit")
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Volcengine Search API returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise RuntimeError("Volcengine Search API returned an unexpected response")
        return result

    @staticmethod
    def _query(query: str, location: str | None, date_range: dict[str, str] | None) -> str:
        parts = [query.strip()]
        if location and location.strip():
            parts.append(location.strip())
        if date_range:
            start, end = date_range.get("start"), date_range.get("end")
            if start and end:
                parts.append(f"活动时间 {start} 至 {end}")
            elif start:
                parts.append(f"{start} 之后的活动")
            elif end:
                parts.append(f"{end} 之前的活动")
        return " ".join(parts).strip()

    def search(
        self,
        query: str,
        location: str | None = None,
        date_range: dict[str, str] | None = None,
    ) -> ConnectorResult:
        if not self.is_available():
            return ConnectorResult(
                self.name, "unavailable", [],
                "VOLCENGINE_SEARCH_API_KEY is not configured.",
            )
        q = self._query(query or "", location, date_range)
        if not q:
            raise ValueError("Search query cannot be empty.")
        if len(q) > 100:
            q = q[:100]

        payload = self._request_json({
            "Query": q,
            "SearchType": "web",
            "DocCount": self.count,
            "MaxSnippetLength": 1000,
        }, self.timeout)

        metadata = payload.get("ResponseMetadata") or {}
        metadata_error = metadata.get("Error") or {}
        result = payload.get("Result")
        if metadata_error:
            code = str(metadata_error.get("Code") or metadata_error.get("CodeN") or "")
            message = str(metadata_error.get("Message") or "provider request failed")
            if code == "10406":
                message = "Monthly free search quota exhausted; no paid fallback was attempted."
            raise RuntimeError(f"Volcengine Search API error {code}: {message}")
        if not isinstance(result, dict):
            raise RuntimeError("Volcengine Search API returned no result payload.")

        result_code = result.get("ErrorCode", 0)
        if result_code not in (0, "0", None):
            result_message = str(result.get("ErrorMsg") or "provider search failed")
            if str(result_code) == "10406":
                result_message = "Monthly free search quota exhausted; no paid fallback was attempted."
            raise RuntimeError(f"Volcengine Search API error {result_code}: {result_message}")

        documents = result.get("Documents") or []
        records: list[dict[str, Any]] = []
        for doc in documents:
            if not isinstance(doc, dict) or not doc.get("Url") or not doc.get("Title"):
                continue
            snippets = doc.get("Snippet") or []
            description = " ".join(
                str(item.get("Text", "")).strip()
                for item in snippets
                if isinstance(item, dict) and item.get("Type") == "text" and item.get("Text")
            ).strip() or None
            host = doc.get("HostInfo") or {}
            info = doc.get("DocumentInfo") or {}
            records.append({
                "title": doc.get("Title"),
                "description": description,
                "source_url": doc.get("Url"),
                "source_platform": self.name,
                "search_provider": "volcengine",
                "published_at": info.get("PublishTime") or None,
                "category": "web-search-candidate",
                "evidence": [{
                    "type": "search_result_snippet",
                    "quote": description,
                    "source_url": doc.get("Url"),
                    "publisher": host.get("Hostname"),
                    "rank": doc.get("Rank"),
                    "authority_level": host.get("AuthorityLevel"),
                }],
                "verification_status": "source_claim",
            })
        return ConnectorResult(
            self.name,
            "ok" if records else "empty",
            records,
            None if records else "No search results.",
        )
