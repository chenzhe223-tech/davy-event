from davy_event.extraction import extract_events


def test_extract_schema_org_event_jsonld():
    payload = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": "Family Art Day",
        "startDate": "2026-12-12T10:00:00+08:00",
        "location": {
            "@type": "Place",
            "name": "National Gallery",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "1 St Andrew's Road",
                "addressLocality": "Singapore",
            },
        },
        "offers": {"price": "12", "priceCurrency": "SGD", "url": "https://tickets.test/family-art"},
    }
    events = extract_events(payload, source_url="https://gallery.test/events/family-art")
    assert len(events) == 1
    assert events[0]["title"] == "Family Art Day"
    assert events[0]["venue_name"] == "National Gallery"
    assert events[0]["city"] == "Singapore"
    assert events[0]["price"] == "12"
    assert events[0]["source_url"] == "https://gallery.test/events/family-art"


def test_extract_schema_org_from_html():
    html = """<html><head><title>Concert listing</title>
    <script type="application/ld+json">{"@type":"Event","name":"Jazz Night","startDate":"2026-12-20T19:00:00+08:00"}</script>
    </head><body>Live jazz</body></html>"""
    events = extract_events(html, source_url="https://music.test/jazz")
    assert events[0]["title"] == "Jazz Night"
    assert events[0]["start_datetime"] == "2026-12-20T19:00:00+08:00"


def test_plain_text_fallback_does_not_guess_missing_date():
    events = extract_events("周末亲子市集，欢迎参加。", source_url="https://events.test/post")
    assert len(events) == 1
    assert events[0]["start_datetime"] is None
    assert events[0]["verification_status"] == "source_claim"


def test_non_event_jsonld_is_ignored():
    assert extract_events({"@type": "Organization", "name": "Example"}) == []


def test_plain_text_extracts_explicit_chinese_datetime():
    events = extract_events(
        "城市周末市集\n活动时间：2026年11月15日 14:30\n欢迎参加",
        source_url="https://events.test/market",
    )
    assert events[0]["title"] == "城市周末市集 活动时间：2026年11月15日 14:30 欢迎参加" or events[0]["title"] == "城市周末市集"
    assert events[0]["start_datetime"] == "2026-11-15T14:30:00"


def test_extracts_explicit_english_date_range_from_title():
    events = extract_events(
        "Things To Do With Kids In Singapore This Weekend: 2 - 8 Nov 2026",
        source_url="https://events.test/kids",
        source_platform="web-search",
    )
    assert events[0]["start_datetime"] == "2026-11-02"
    assert events[0]["end_datetime"] == "2026-11-08"


def test_extracts_english_date_range_from_html_title_and_meta():
    html = """<html><head>
    <title>Family events: 2–8 Nov 2026</title>
    <meta name="description" content="Events across Singapore this week." />
    </head><body>Family activities</body></html>"""
    events = extract_events(html, source_url="https://events.test/week")
    assert events[0]["start_datetime"] == "2026-11-02"
    assert events[0]["end_datetime"] == "2026-11-08"
