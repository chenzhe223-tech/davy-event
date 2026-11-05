from davy_event.discovery import (
    discover_events, register_connector, unregister_connector,
)
from davy_event.connectors import ConnectorResult


class MockConnector:
    name = "mock-web"

    def is_available(self):
        return True

    def search(self, query, location=None, date_range=None):
        assert query == "weekend market"
        return ConnectorResult(
            platform=self.name,
            status="ok",
            records=[{
                "title": "Weekend Market",
                "start_datetime": "2026-11-07T10:00:00+08:00",
                "source_url": "https://example.test/event",
            }],
        )


class BrokenConnector:
    name = "broken"

    def is_available(self):
        return True

    def search(self, query, location=None, date_range=None):
        raise TimeoutError("provider timed out")


def test_discovery_normalizes_records_and_reports_coverage():
    result = discover_events("weekend market", [MockConnector()], location="Singapore")
    assert result["status"] == "ok"
    assert result["events"][0]["title"] == "Weekend Market"
    assert result["events"][0]["source_platform"] == "mock-web"
    assert result["coverage"][0]["records_count"] == 1


def test_discovery_without_connectors_is_explicitly_unavailable():
    result = discover_events("concert", platforms=["xiaohongshu", "douyin"])
    assert result["status"] == "unavailable"
    assert result["events"] == []
    assert {x["platform"] for x in result["coverage"]} == {"xiaohongshu", "douyin"}


def test_one_connector_failure_does_not_hide_other_results():
    result = discover_events("weekend market", [BrokenConnector(), MockConnector()])
    assert result["status"] == "ok"
    assert len(result["events"]) == 1
    assert result["coverage"][0]["status"] == "error"


def test_registered_connectors_are_used_by_default():
    connector = MockConnector()
    register_connector(connector)
    try:
        result = discover_events("weekend market")
        assert result["status"] == "ok"
        assert result["events"][0]["title"] == "Weekend Market"
    finally:
        unregister_connector(connector.name)
