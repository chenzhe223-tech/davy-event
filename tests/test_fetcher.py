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
