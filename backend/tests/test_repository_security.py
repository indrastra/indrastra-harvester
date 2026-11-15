import socket

import pytest

from backend.app.repositories.security import validate_public_http_endpoint


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.org/oai",
        "http://localhost/oai",
        "http://127.0.0.1/oai",
        "http://10.0.0.1/oai",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/oai",
        "https://user:pass@example.org/oai",
        "https://example.org:8443/oai",
    ],
)
def test_rejects_unsafe_endpoint_forms(url):
    with pytest.raises(ValueError):
        validate_public_http_endpoint(url)


def test_accepts_public_literal_ip():
    assert validate_public_http_endpoint("https://1.1.1.1/oai") == "https://1.1.1.1/oai"


def test_rejects_fragment():
    with pytest.raises(ValueError, match="fragments"):
        validate_public_http_endpoint("https://example.org/oai#fragment")


def test_rejects_hostname_with_any_private_dns_answer(monkeypatch):
    def fake_getaddrinfo(*args, **kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.9", 443)),
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(ValueError, match="non-public"):
        validate_public_http_endpoint("https://mixed-answer.example/oai")
