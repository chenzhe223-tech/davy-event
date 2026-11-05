"""Platform-neutral event normalization and quality utilities."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Any, Iterable


def _clean(value: Any) -> Any:
    if isinstance(value, str):
        value = re.sub(r"\s+", " ", value).strip()
        return value or None
    return value


def normalize_event(raw: dict[str, Any], source: str | None = None) -> dict[str, Any]:
    """Normalize a source record without inventing missing facts."""
    now = datetime.now(timezone.utc).isoformat()
    aliases = {
        "title": ("title", "name", "活动名称", "活动标题"),
        "start_datetime": ("start_datetime", "start_time", "开始时间", "活动时间"),
        "end_datetime": ("end_datetime", "end_time", "结束时间"),
        "timezone": ("timezone", "时区"),
        "venue_name": ("venue_name", "venue", "场地", "商家名称"),
        "address": ("address", "地址", "详细地址"),
        "city": ("city", "城市"),
        "price": ("price", "价格", "费用"),
        "currency": ("currency", "币种"),
        "category": ("category", "类别", "活动类型"),
        "organizer": ("organizer", "主办方"),
        "registration_url": ("registration_url", "报名链接", "购票链接"),
        "source_url": ("source_url", "url", "原文链接", "链接"),
        "description": ("description", "summary", "活动介绍", "描述"),
    }
    result: dict[str, Any] = {}
    for target, keys in aliases.items():
        result[target] = next((_clean(raw[k]) for k in keys if k in raw and _clean(raw[k]) is not None), None)
    result.update({
        "source_platform": source or raw.get("source_platform") or "unknown",
        "retrieved_at": raw.get("retrieved_at") or now,
        "evidence": raw.get("evidence") or [],
        "verification_status": raw.get("verification_status") or "source_claim",
        "confidence": raw.get("confidence"),
        "event_id": raw.get("event_id"),
    })
    return result


def _identity(event: dict[str, Any]) -> tuple[str, str, str]:
    title = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", (event.get("title") or "").lower())
    venue = re.sub(r"\s+", "", (event.get("venue_name") or event.get("address") or "").lower())
    start = (event.get("start_datetime") or "")[:16]
    return title, venue, start


def deduplicate_events(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Conservatively merge exact identity matches; preserve every source URL."""
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for event in events:
        key = _identity(event)
        if not key[0]:
            # Records without a title cannot be safely merged.
            key = (f"__untitled_{len(merged)}", key[1], key[2])
        if key not in merged:
            item = dict(event)
            item["source_urls"] = [event["source_url"]] if event.get("source_url") else []
            merged[key] = item
            continue
        item = merged[key]
        for field, value in event.items():
            if item.get(field) in (None, "", []) and value not in (None, "", []):
                item[field] = value
        url = event.get("source_url")
        if url and url not in item["source_urls"]:
            item["source_urls"].append(url)
        if event.get("evidence"):
            combined = item.get("evidence", []) + event["evidence"]
            unique: list[Any] = []
            seen: set[str] = set()
            for evidence_item in combined:
                fingerprint = json.dumps(evidence_item, ensure_ascii=False, sort_keys=True, default=str)
                if fingerprint not in seen:
                    seen.add(fingerprint)
                    unique.append(evidence_item)
            item["evidence"] = unique
    return list(merged.values())


def verify_event(event: dict[str, Any], evidence: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Apply transparent completeness checks; this does not independently browse."""
    evidence = evidence if evidence is not None else event.get("evidence", [])
    required = ("title", "start_datetime", "source_url")
    missing = [field for field in required if not event.get(field)]
    result = dict(event)
    result["evidence"] = evidence
    if missing:
        result["verification_status"] = "uncertain"
        result["verification_notes"] = {"missing_required_fields": missing}
    elif len(evidence) >= 2:
        result["verification_status"] = "verified" if any(x.get("primary_source") for x in evidence if isinstance(x, dict)) else "source_claim"
        result["verification_notes"] = {"evidence_count": len(evidence), "independent_corroboration_not_guaranteed": True}
    else:
        result["verification_status"] = "source_claim"
        result["verification_notes"] = {"evidence_count": len(evidence)}
    return result


def export_events(events: Iterable[dict[str, Any]], format: str = "json") -> str:
    records = list(events)
    if format == "json":
        return json.dumps(records, ensure_ascii=False, indent=2)
    if format == "jsonl":
        return "\n".join(json.dumps(x, ensure_ascii=False) for x in records)
    raise ValueError("Supported formats: json, jsonl")
