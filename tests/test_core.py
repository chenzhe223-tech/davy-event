from davy_event import normalize_event, deduplicate_events, verify_event, export_events


def test_normalize_preserves_unknowns_as_none():
    event = normalize_event({"活动名称": " 周末市集 ", "原文链接": "https://example.com/e"}, "web")
    assert event["title"] == "周末市集"
    assert event["start_datetime"] is None
    assert event["source_platform"] == "web"


def test_deduplicate_same_event_and_keep_sources():
    a = normalize_event({"title": "Art Fair", "start_datetime": "2026-11-07T10:00:00+08:00", "source_url": "https://a.test"}, "web")
    b = normalize_event({"title": "Art Fair", "start_datetime": "2026-11-07T10:00:00+08:00", "source_url": "https://b.test"}, "social")
    result = deduplicate_events([a, b])
    assert len(result) == 1
    assert set(result[0]["source_urls"]) == {"https://a.test", "https://b.test"}


def test_verify_flags_missing_fields():
    result = verify_event({"title": "Event", "source_url": None, "start_datetime": None})
    assert result["verification_status"] == "uncertain"


def test_export_json():
    assert '"title": "Demo"' in export_events([{"title": "Demo"}])
