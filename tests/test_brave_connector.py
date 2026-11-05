from davy_event.connectors.brave import BraveSearchConnector


def test_brave_connector_maps_search_results():
    captured = {}
    def fake_request(url, headers, timeout):
        captured.update({"url": url, "headers": headers, "timeout": timeout})
        return {"web": {"results": [
            {"title": "Family Art Weekend", "url": "https://gallery.example/events/1", "description": "A family art event."},
            {"title": "Malformed result"},
        ]}}
    connector = BraveSearchConnector("test-token", country="SG", request_json=fake_request)
    result = connector.search("family art", location="Singapore")
    assert result.status == "ok"
    assert len(result.records) == 1
    assert result.records[0]["title"] == "Family Art Weekend"
    assert result.records[0]["verification_status"] == "source_claim"
    assert "X-Subscription-Token" in captured["headers"]
    assert "family+art+Singapore" in captured["url"]


def test_brave_connector_without_key_is_unavailable():
    connector = BraveSearchConnector(api_key="")
    assert connector.is_available() is False
    result = connector.search("music festival")
    assert result.status == "unavailable"
    assert result.records == []


def test_brave_connector_rejects_empty_and_oversized_query():
    connector = BraveSearchConnector("test-token", request_json=lambda *a: {})
    import pytest
    with pytest.raises(ValueError):
        connector.search(" ")
    with pytest.raises(ValueError):
        connector.search("x" * 601)
