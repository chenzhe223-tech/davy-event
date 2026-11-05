"""Brave Search API connector for public web event discovery."""
from __future__ import annotations

import json
import os
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from davy_event.connectors import ConnectorResult


class BraveSearchConnector:
    name = "web-search"
    endpoint = "https://api.search.brave.com/res/v1/web/search"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        country: str = "SG",
        search_lang: str = "en",
        count: int = 10,
        timeout: float = 12.0,
        request_json: Callable[..., dict[str, Any]] | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("BRAVE_SEARCH_API_KEY")
        self.country = country.upper()
        self.search_lang = search_lang
        self.count = max(1, min(int(count), 20))
        self.timeout = timeout
        self._request_json = request_json or self._http_request_json

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _http_request_json(self, url: str, headers: dict[str, str], timeout: float) -> dict[str, Any]:
        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = response.read(2_000_001)
        except HTTPError as exc:
            raise RuntimeError(f"Brave Search API returned HTTP {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError("Brave Search API request failed") from exc
        if len(payload) > 2_000_000:
            raise RuntimeError("Brave Search API response exceeded the size limit")
        try:
            parsed = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Brave Search API returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("Brave Search API returned an unexpected response")
        return parsed

    def search(
        self,
        query: str,
        location: str | None = None,
        date_range: dict[str, str] | None = None,
    ) -> ConnectorResult:
        if not self.is_available():
            return ConnectorResult(self.name, "unavailable", [], "BRAVE_SEARCH_API_KEY is not configured.")
        q = (query or "").strip()
        if location:
            q = f"{q} {location.strip()}".strip()
        if date_range:
            start, end = date_range.get("start"), date_range.get("end")
            if start:
                q += f" after:{start}"
            if end:
                q += f" before:{end}"
        if not q:
            raise ValueError("Search query cannot be empty.")
        if len(q) > 600:
            raise ValueError("Search query must be 600 characters or fewer.")
        params = urlencode({"q": q, "count": self.count, "country": self.country, "search_lang": self.search_lang})
        payload = self._request_json(
            f"{self.endpoint}?{params}",
            {"Accept": "application/json", "X-Subscription-Token": self.api_key or ""},
            self.timeout,
        )
        web = payload.get("web") or {}
        results = web.get("results") or []
        records: list[dict[str, Any]] = []
        for item in results:
            if not isinstance(item, dict) or not item.get("url") or not item.get("title"):
                continue
            records.append({
                "title": item.get("title"),
                "description": item.get("description"),
                "source_url": item.get("url"),
                "source_platform": self.name,
                "category": "web-search-candidate",
                "evidence": [{
                    "type": "search_result_snippet",
                    "quote": item.get("description"),
                    "source_url": item.get("url"),
                    "publisher": item.get("profile", {}).get("long_name") if isinstance(item.get("profile"), dict) else None,
                }],
                "verification_status": "source_claim",
            })
        return ConnectorResult(self.name, "ok" if records else "empty", records, None if records else "No search results.")
