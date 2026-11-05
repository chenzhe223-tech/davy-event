"""SSRF-resistant, size-limited public HTTP(S) fetcher.

Connections are pinned to a validated public IP address to avoid a second DNS
lookup after validation. Redirects are handled manually and revalidated.
"""
from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit, urlunsplit


ALLOWED_CONTENT_TYPES = {
    "text/html", "application/xhtml+xml", "text/plain", "application/ld+json"
}
REDIRECT_CODES = {301, 302, 303, 307, 308}


class UnsafeURLError(ValueError):
    """The requested URL or its resolved destination violates fetch policy."""


@dataclass
class FetchResult:
    requested_url: str
    final_url: str
    status_code: int
    content_type: str
    text: str
    byte_count: int


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, port: int, pinned_ip: str, timeout: float, context: ssl.SSLContext):
        super().__init__(pinned_ip, port=port, timeout=timeout, context=context)
        self._pinned_ip = pinned_ip
        self._server_hostname = host
        self._ssl_context = context

    def connect(self) -> None:
        raw = socket.create_connection((self._pinned_ip, self.port), self.timeout)
        self.sock = self._ssl_context.wrap_socket(raw, server_hostname=self._server_hostname)


def _validated_target(url: str, resolver=socket.getaddrinfo) -> tuple[str, str, int, str]:
    try:
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"}:
            raise UnsafeURLError("Only HTTP and HTTPS URLs are allowed.")
        if not parsed.hostname or "%" in parsed.hostname or parsed.username is not None or parsed.password is not None:
            raise UnsafeURLError("URL must contain a hostname and no embedded credentials.")
        if parsed.fragment:
            url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))
            parsed = urlsplit(url)
        host = parsed.hostname.rstrip(".").lower()
        port = parsed.port or (443 if scheme == "https" else 80)
        if port not in ({443} if scheme == "https" else {80}):
            raise UnsafeURLError("Only standard HTTP/HTTPS ports are allowed.")
        try:
            literal = ipaddress.ip_address(host)
            addresses = [str(literal)]
        except ValueError:
            if not host or host == "localhost" or "." not in host:
                raise UnsafeURLError("Local and single-label hostnames are not allowed.")
            try:
                resolved = resolver(host, port, type=socket.SOCK_STREAM)
            except OSError as exc:
                raise UnsafeURLError("Hostname could not be resolved.") from exc
            addresses = list(dict.fromkeys(item[4][0] for item in resolved))
        if not addresses:
            raise UnsafeURLError("Hostname did not resolve to an address.")
        parsed_ips = [ipaddress.ip_address(item.split("%", 1)[0]) for item in addresses]
        if any(not item.is_global for item in parsed_ips):
            raise UnsafeURLError("Host resolves to a non-public IP address.")
        # Pin one of the validated addresses; no later DNS lookup is performed.
        pinned = str(parsed_ips[0])
        return scheme, host, port, pinned
    except UnsafeURLError:
        raise
    except (ValueError, TypeError) as exc:
        raise UnsafeURLError("Malformed URL.") from exc


def fetch_public_url(
    url: str,
    *,
    timeout: float = 10.0,
    max_bytes: int = 1_000_000,
    max_redirects: int = 3,
    resolver=socket.getaddrinfo,
    connection_factory=None,
) -> FetchResult:
    if not isinstance(url, str) or len(url) > 2048:
        raise UnsafeURLError("URL must be a string no longer than 2048 characters.")
    requested_url = url
    current = url
    for hop in range(max_redirects + 1):
        scheme, host, port, pinned_ip = _validated_target(current, resolver=resolver)
        parsed = urlsplit(current)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        host_label = f"[{host}]" if ":" in host else host
        host_header = host_label if port in (80, 443) else f"{host_label}:{port}"
        if connection_factory is not None:
            connection = connection_factory(scheme, host, port, pinned_ip, timeout)
        elif scheme == "https":
            connection = _PinnedHTTPSConnection(host, port, pinned_ip, timeout, ssl.create_default_context())
        else:
            connection = http.client.HTTPConnection(pinned_ip, port=port, timeout=timeout)
        try:
            connection.request("GET", path, headers={
                "Host": host_header,
                "User-Agent": "DAVYLAB-EventRadar/0.5 (+https://github.com/chenzhe223-tech/davy-event)",
                "Accept": "text/html,application/xhtml+xml,text/plain,application/ld+json",
                "Accept-Encoding": "identity",
                "Connection": "close",
            })
            response = connection.getresponse()
            if response.status in REDIRECT_CODES:
                location = response.getheader("Location")
                response.read(8192)
                if not location:
                    raise RuntimeError("Redirect response did not include a Location header.")
                if hop >= max_redirects:
                    raise RuntimeError("Maximum redirect count exceeded.")
                current = urljoin(current, location)
                continue
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"Remote server returned HTTP {response.status}.")
            content_type = (response.getheader("Content-Type") or "").split(";", 1)[0].strip().lower()
            if content_type not in ALLOWED_CONTENT_TYPES:
                raise RuntimeError(f"Unsupported content type: {content_type or 'missing'}.")
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise RuntimeError("Remote content exceeded the configured size limit.")
            charset = "utf-8"
            content_header = response.getheader("Content-Type") or ""
            for part in content_header.split(";")[1:]:
                if part.strip().lower().startswith("charset="):
                    charset = part.split("=", 1)[1].strip().strip('"')[:40]
            try:
                text = raw.decode(charset, errors="replace")
            except LookupError:
                text = raw.decode("utf-8", errors="replace")
            return FetchResult(requested_url, current, response.status, content_type, text, len(raw))
        finally:
            connection.close()
    raise RuntimeError("Unable to fetch URL.")
