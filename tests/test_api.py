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
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    client = TestClient(create_app())
    response = client.post("/discover", json={"query": "family events", "platforms": ["web-search"]})
    assert response.status_code == 200
    assert response.json()["coverage"][0]["status"] == "unavailable"


def test_fetch_rejects_private_destination():
    client = TestClient(create_app())
    response = client.post("/fetch", json={"url": "http://127.0.0.1/"})
    assert response.status_code == 400
