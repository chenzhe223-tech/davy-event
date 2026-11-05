from fastapi.testclient import TestClient
from davy_event.api import create_app


def test_health_and_extract_api():
    client = TestClient(create_app())
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    response = client.post("/extract", json={
        "content": "社区艺术节\n活动时间：2026年12月20日 10:00",
        "source_url": "https://events.example/festival",
    })
    assert response.status_code == 200
    assert response.json()["events"][0]["start_datetime"] == "2026-12-20T10:00:00"


def test_discover_reports_missing_search_key_honestly(monkeypatch):
    monkeypatch.delenv("VOLCENGINE_SEARCH_API_KEY", raising=False)
    client = TestClient(create_app())
    response = client.post("/discover", json={"query": "family events", "platforms": ["web-search"]})
    assert response.status_code == 200
    assert response.json()["coverage"][0]["status"] == "unavailable"


def test_fetch_rejects_private_destination():
    client = TestClient(create_app())
    response = client.post("/fetch", json={"url": "http://127.0.0.1/"})
    assert response.status_code == 400


def test_discover_enriches_search_candidates_with_fetched_event(monkeypatch):
    from types import SimpleNamespace
    import davy_event.api as api

    class FakeConnector:
        name = "web-search"
        def is_available(self):
            return True
        def search(self, query, location=None, date_range=None):
            from davy_event.connectors import ConnectorResult
            return ConnectorResult("web-search", "ok", [{
                "title": "Search result title",
                "description": "A clue",
                "source_url": "https://events.example/page",
            }])

    monkeypatch.setattr(api, "fetch_public_url", lambda url: SimpleNamespace(
        text='<html><head><script type="application/ld+json">{"@type":"Event","name":"Official Open Day","startDate":"2026-12-20T10:00:00+08:00"}</script></head><body>Open day</body></html>',
        final_url=url,
        content_type="text/html",
        byte_count=200,
    ))
    client = TestClient(create_app())
    from davy_event.discovery import register_connector, unregister_connector
    register_connector(FakeConnector())
    try:
        response = client.post("/discover", json={"query": "open day", "platforms": ["web-search"]})
        assert response.status_code == 200
        event = response.json()["events"][0]
        assert event["start_datetime"] == "2026-12-20T10:00:00+08:00"
        assert event["fetch_status"] == "fetched"
        assert event["verification_status"] == "source_claim"
    finally:
        unregister_connector("web-search")


def test_connectors_endpoint_reports_platform_gaps():
    client = TestClient(create_app())
    response = client.get("/connectors")
    assert response.status_code == 200
    status = {item["platform"]: item["status"] for item in response.json()["connectors"]}
    assert "web-search" in status
    assert status["xiaohongshu"] == "unavailable"
    assert status["douyin"] == "unavailable"
    assert status["dianping"] == "unavailable"


def test_api_token_protects_non_health_routes(monkeypatch):
    monkeypatch.setenv("DAVY_EVENT_API_TOKEN", "test-secret")
    client = TestClient(create_app())
    assert client.get("/health").status_code == 200
    assert client.get("/connectors").status_code == 401
    assert client.get("/connectors", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/connectors", headers={"Authorization": "Bearer test-secret"}).status_code == 200


def test_render_fails_closed_when_api_token_is_not_configured(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("DAVY_EVENT_API_TOKEN", raising=False)
    client = TestClient(create_app())
    assert client.get("/health").status_code == 200
    response = client.get("/connectors")
    assert response.status_code == 503
    assert "DAVY_EVENT_API_TOKEN" in response.json()["detail"]

def test_openapi_exposes_bearer_auth_for_protected_routes(monkeypatch):
    monkeypatch.setenv("DAVY_EVENT_API_TOKEN", "test-secret")
    client = TestClient(create_app())

    docs = client.get("/docs")
    schema = client.get("/openapi.json")

    assert docs.status_code == 200
    assert schema.status_code == 200
    openapi = schema.json()
    assert openapi["components"]["securitySchemes"]["BearerAuth"] == {
        "type": "http",
        "scheme": "bearer",
        "description": "Enter the DAVY_EVENT_API_TOKEN value. Do not include the 'Bearer ' prefix.",
    }
    assert openapi["paths"]["/connectors"]["get"]["security"] == [{"BearerAuth": []}]
    assert "security" not in openapi["paths"]["/health"]["get"]
\n
