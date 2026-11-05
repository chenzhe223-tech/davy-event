import pytest

from davy_event.connectors.volcengine import VolcengineSearchConnector


def test_missing_key_reports_unavailable(monkeypatch):
    monkeypatch.delenv("VOLCENGINE_SEARCH_API_KEY", raising=False)
    connector = VolcengineSearchConnector()
    assert connector.is_available() is False
    result = connector.search("周末亲子活动", location="新加坡")
    assert result.status == "unavailable"
    assert "VOLCENGINE_SEARCH_API_KEY" in result.message


def test_search_maps_official_global_response():
    captured = {}

    def fake_request(payload, timeout):
        captured["payload"] = payload
        captured["timeout"] = timeout
        return {
            "ResponseMetadata": {"RequestId": "req-1"},
            "Result": {
                "ErrorCode": 0,
                "Documents": [{
                    "Rank": 0,
                    "Url": "https://events.example/family-day",
                    "Title": "Family Day",
                    "Snippet": [
                        {"Type": "text", "Text": "Family event this Saturday."},
                        {"Type": "image", "Image": {"ImageUrl": "https://img.example/poster.jpg"}},
                    ],
                    "DocumentInfo": {"PublishTime": "2026-11-01"},
                    "HostInfo": {"Hostname": "Example Events", "AuthorityLevel": "high"},
                }],
            },
        }

    connector = VolcengineSearchConnector(
        api_key="test-key", count=7, request_json=fake_request
    )
    result = connector.search(
        "亲子活动", location="新加坡",
        date_range={"start": "2026-11-07", "end": "2026-11-08"},
    )
    assert result.status == "ok"
    assert result.platform == "web-search"
    assert len(result.records) == 1
    record = result.records[0]
    assert record["title"] == "Family Day"
    assert record["description"] == "Family event this Saturday."
    assert record["source_url"] == "https://events.example/family-day"
    assert record["published_at"] == "2026-11-01"
    assert record["verification_status"] == "source_claim"
    assert record["evidence"][0]["publisher"] == "Example Events"
    assert captured["payload"]["SearchType"] == "web"
    assert captured["payload"]["DocCount"] == 7
    assert "新加坡" in captured["payload"]["Query"]
    assert "2026-11-07" in captured["payload"]["Query"]


def test_empty_search_response_is_empty():
    connector = VolcengineSearchConnector(
        api_key="test-key",
        request_json=lambda payload, timeout: {
            "ResponseMetadata": {},
            "Result": {"ErrorCode": 0, "Documents": []},
        },
    )
    result = connector.search("周末活动")
    assert result.status == "empty"
    assert result.records == []


def test_free_quota_exhaustion_never_falls_back_to_paid_provider():
    connector = VolcengineSearchConnector(
        api_key="test-key",
        request_json=lambda payload, timeout: {
            "ResponseMetadata": {
                "Error": {"Code": "10406", "Message": "quota exhausted"}
            },
            "Result": None,
        },
    )
    with pytest.raises(RuntimeError, match="Monthly free search quota exhausted"):
        connector.search("周末活动")


def test_query_is_clamped_to_provider_limit():
    captured = {}
    connector = VolcengineSearchConnector(
        api_key="test-key",
        request_json=lambda payload, timeout: (
            captured.update(payload) or {
                "ResponseMetadata": {},
                "Result": {"ErrorCode": 0, "Documents": []},
            }
        ),
    )
    connector.search("活动" * 80)
    assert len(captured["Query"]) == 100
