"""Extract event candidates from supplied HTML, JSON-LD, dictionaries, or plain text.

This module performs no network requests. Fetching a URL is the host application's
responsibility; pass the returned page content and its canonical URL here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import re
from typing import Any

from .core import normalize_event


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.jsonld: list[Any] = []
        self.meta: dict[str, str] = {}
        self.title_parts: list[str] = []
        self._in_jsonld = False
        self._in_title = False
        self._script_parts: list[str] = []
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "script" and values.get("type", "").lower() == "application/ld+json":
            self._in_jsonld = True
            self._script_parts = []
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() == "meta":
            key = values.get("property") or values.get("name")
            content = values.get("content")
            if key and content:
                self.meta[key.lower()] = content.strip()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_jsonld:
            raw = "".join(self._script_parts).strip()
            if raw:
                try:
                    self.jsonld.append(json.loads(raw))
                except json.JSONDecodeError:
                    pass
            self._in_jsonld = False
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_jsonld:
            self._script_parts.append(data)
        elif data.strip():
            self._text_parts.append(data.strip())
            if self._in_title:
                self.title_parts.append(data.strip())


def _walk_jsonld(value: Any):
    if isinstance(value, list):
        for item in value:
            yield from _walk_jsonld(item)
    elif isinstance(value, dict):
        graph = value.get("@graph")
        if graph is not None:
            yield from _walk_jsonld(graph)
        else:
            yield value
        for key in ("mainEntity", "itemListElement", "subEvent", "item", "itemOffered", "subjectOf"):
            if key in value:
                yield from _walk_jsonld(value[key])


def _types(obj: dict[str, Any]) -> set[str]:
    raw = obj.get("@type", [])
    if isinstance(raw, str):
        raw = [raw]
    return {str(x).rsplit("/", 1)[-1].lower() for x in raw}


def _name(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("name")
    return value


def _event_from_jsonld(obj: dict[str, Any], source_url: str | None, platform: str) -> dict[str, Any]:
    location = obj.get("location") or {}
    address = location.get("address") if isinstance(location, dict) else None
    if isinstance(address, dict):
        address_text = ", ".join(str(address[k]) for k in ("streetAddress", "addressLocality", "addressRegion", "postalCode", "addressCountry") if address.get(k))
        city = address.get("addressLocality")
    else:
        address_text = address
        city = None
    offers = obj.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    if not isinstance(offers, dict):
        offers = {}
    price = offers.get("price")
    currency = offers.get("priceCurrency")
    return normalize_event({
        "title": obj.get("name"),
        "description": obj.get("description"),
        "start_datetime": obj.get("startDate"),
        "end_datetime": obj.get("endDate"),
        "timezone": obj.get("eventSchedule", {}).get("scheduleTimezone") if isinstance(obj.get("eventSchedule"), dict) else None,
        "venue_name": _name(location),
        "address": address_text,
        "city": city,
        "price": price,
        "currency": currency,
        "category": _name(obj.get("about")) or obj.get("eventAttendanceMode"),
        "organizer": _name(obj.get("organizer")),
        "registration_url": offers.get("url"),
        "source_url": source_url or obj.get("url"),
        "evidence": [{"type": "schema.org/Event", "source_url": source_url or obj.get("url")}],
    }, platform)


def _find_start_datetime(text: str) -> str | None:
    iso = re.search(r"(?<!\d)(20\d{2}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:?\d{2})?)?)", text)
    if iso:
        return iso.group(1)
    chinese = re.search(r"(20\d{2})年(\d{1,2})月(\d{1,2})日(?:\s*(\d{1,2}):(\d{2}))?", text)
    if chinese:
        year, month, day, hour, minute = chinese.groups()
        value = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        return f"{value}T{int(hour):02d}:{minute}:00" if hour is not None else value
    slash = re.search(r"(?<!\d)(20\d{2})/(\d{1,2})/(\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?", text)
    if slash:
        year, month, day, hour, minute = slash.groups()
        value = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        return f"{value}T{int(hour):02d}:{minute}:00" if hour is not None else value
    return None

def _find_date_range(text: str) -> tuple[str | None, str | None]:
    """Parse explicit English date ranges such as 2–8 Nov 2026 without guessing a year."""
    month = r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    patterns = [
        rf"(?<!\d)(\d{{1,2}})\s*[-–—]\s*(\d{{1,2}})\s+{month}\s+(20\d{{2}})(?!\d)",
        rf"(?<!\d){month}\s+(\d{{1,2}})\s*[-–—]\s*(\d{{1,2}}),?\s+(20\d{{2}})(?!\d)",
    ]
    for index, pattern in enumerate(patterns):
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        try:
            if index == 0:
                first, last, month_name, year = match.groups()
            else:
                month_name, first, last, year = match.groups()
            month_number = datetime.strptime(month_name[:3].title(), "%b").month
            start = datetime(int(year), month_number, int(first)).date().isoformat()
            end = datetime(int(year), month_number, int(last)).date().isoformat()
            return start, end
        except ValueError:
            continue
    return None, None


def extract_events(content: str | dict[str, Any] | list[Any], *,
                   source_url: str | None = None,
                   source_platform: str = "user-provided") -> list[dict[str, Any]]:
    """Extract event records from supplied content; never invent absent fields."""
    if isinstance(content, (dict, list)):
        candidates = list(_walk_jsonld(content))
        return [
            _event_from_jsonld(item, source_url, source_platform)
            for item in candidates if isinstance(item, dict) and "event" in _types(item)
        ]

    text = content or ""
    parser = _PageParser()
    is_html = bool(re.search(r"<(?:html|head|body|script|meta|title)\b", text, re.I))
    if is_html:
        parser.feed(text)
        candidates = [item for block in parser.jsonld for item in _walk_jsonld(block)]
        events = [
            _event_from_jsonld(item, source_url, source_platform)
            for item in candidates if isinstance(item, dict) and "event" in _types(item)
        ]
        if events:
            return events
        page_title = parser.meta.get("og:title") or parser.meta.get("twitter:title") or " ".join(parser.title_parts)
        description = parser.meta.get("og:description") or parser.meta.get("description")
        visible_text = " ".join(parser._text_parts)
    else:
        page_title = ""
        description = None
        visible_text = text.strip()

    if not visible_text and not page_title:
        return []
    # Deterministic fallback: parse only explicit dates; never infer a year.
    date_text = " ".join(part for part in (page_title, description or "", visible_text) if part)
    start_datetime, end_datetime = _find_date_range(date_text)
    if start_datetime is None:
        start_datetime = _find_start_datetime(date_text)
    first_line = next((line.strip() for line in visible_text.splitlines() if line.strip()), "")
    title = page_title or (first_line[:100] if first_line else None)
    record = normalize_event({
        "title": title,
        "description": description or visible_text[:1000] or None,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "source_url": source_url,
        "evidence": [{"type": "page_text", "source_url": source_url, "retrieved_at": datetime.now(timezone.utc).isoformat()}],
    }, source_platform)
    return [record] if record.get("title") else []
