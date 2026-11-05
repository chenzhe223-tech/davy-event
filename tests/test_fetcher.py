import socket
import pytest
from davy_event.fetcher import UnsafeURLError, _validated_target


def test_fetcher_rejects_non_http_protocols():
    with pytest.raises(UnsafeURLError):
        _validated_target("file:///etc/passwd")


def test_fetcher_rejects_credentials():
    with pytest.raises(UnsafeURLError):
        _validated_target("https://user:pass@example.com/")


def test_fetcher_rejects_localhost():
    with pytest.raises(UnsafeURLError):
        _validated_target("http://localhost/")


def test_fetcher_rejects_private_ip_literal():
    with pytest.raises(UnsafeURLError):
        _validated_target("http://127.0.0.1/")


def test_fetcher_rejects_dns_rebinding_mixed_public_private_answers():
    def resolver(host, port, type):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", port)),
        ]
    with pytest.raises(UnsafeURLError):
        _validated_target("https://events.example/", resolver=resolver)


def test_fetcher_accepts_public_dns_and_returns_pinned_ip():
    def resolver(host, port, type):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
    scheme, host, port, ip = _validated_target("https://events.example/path", resolver=resolver)
    assert (scheme, host, port, ip) == ("https", "events.example", 443, "93.184.216.34")


class FakeResponse:
    def __init__(self, status=200, headers=None, body=b"<html><title>Open Day</title></html>"):
        self.status = status
        self.headers = headers or {"Content-Type": "text/html; charset=utf-8"}
        self.body = body

    def getheader(self, name):
        return self.headers.get(name)

    def read(self, amount=-1):
        return self.body[:amount] if amount >= 0 else self.body


class FakeConnection:
    def __init__(self, response):
        self.response = response
        self.requested = None

    def request(self, method, path, headers):
        self.requested = (method, path, headers)

    def getresponse(self):
        return self.response

    def close(self):
        pass


def test_fetcher_uses_pinned_public_ip_and_returns_html():
    def resolver(host, port, type):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
    connections = []
    def factory(scheme, host, port, pinned_ip, timeout):
        assert pinned_ip == "93.184.216.34"
        conn = FakeConnection(FakeResponse(body=b"<html><title>Open Day</title></html>"))
        connections.append(conn)
        return conn
    from davy_event.fetcher import fetch_public_url
    result = fetch_public_url("https://events.example/open", resolver=resolver, connection_factory=factory)
    assert result.status_code == 200
    assert result.content_type == "text/html"
    assert "Open Day" in result.text
    assert connections[0].requested[2]["Host"] == "events.example"


def test_fetcher_revalidates_redirect_destination():
    def resolver(host, port, type):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
    calls = []
    def factory(scheme, host, port, pinned_ip, timeout):
        calls.append(host)
        return FakeConnection(FakeResponse(
            status=302,
            headers={"Location": "http://127.0.0.1/admin", "Content-Type": "text/plain"},
            body=b"",
        ))
    from davy_event.fetcher import fetch_public_url
    with pytest.raises(UnsafeURLError):
        fetch_public_url("https://events.example/redirect", resolver=resolver, connection_factory=factory)
    assert calls == ["events.example"]
