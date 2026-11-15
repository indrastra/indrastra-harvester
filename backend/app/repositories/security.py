"""Outbound endpoint validation for user-supplied repository URLs.

This is a first security gate, not a substitute for network-level egress controls.
DNS is checked before requests, but a separate DNS lookup by the HTTP stack can
still create a DNS-rebinding window. Production deployments must additionally
enforce outbound firewall/egress-proxy rules.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit

from fastapi import HTTPException


class UnsafeEndpointError(ValueError):
    """Raised when a repository endpoint could reach a prohibited destination."""


def validate_public_http_endpoint(value: str) -> str:
    raw = value.strip()
    parsed = urlsplit(raw)

    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Endpoint must use HTTP or HTTPS.")
    if not parsed.hostname:
        raise ValueError("Endpoint must include a hostname.")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in endpoint URLs are prohibited.")
    if parsed.fragment:
        raise ValueError("Endpoint URLs must not contain fragments.")

    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Endpoint contains an invalid port.") from exc

    if port not in (None, 80, 443):
        raise ValueError("Only standard HTTP (80) and HTTPS (443) ports are permitted.")

    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        raise ValueError("Localhost endpoints are prohibited.")

    netloc_host = host
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        try:
            records = socket.getaddrinfo(
                host,
                port or (443 if parsed.scheme.lower() == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise ValueError("Endpoint hostname could not be resolved.") from exc
        addresses = {item[4][0] for item in records}
        if not addresses:
            raise ValueError("Endpoint hostname has no address records.")
        for address in addresses:
            _require_global_address(address)
    else:
        _require_global_address(str(literal))
        if literal.version == 6:
            netloc_host = f"[{host}]"

    netloc = netloc_host
    if port is not None:
        netloc = f"{netloc_host}:{port}"
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, ""))


def _require_global_address(value: str) -> None:
    address = ipaddress.ip_address(value)
    if not address.is_global:
        raise ValueError("Endpoint resolves to a non-public IP address, which is prohibited.")
    if (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise ValueError("Endpoint resolves to a prohibited IP address.")


def ensure_endpoint_is_safe(endpoint: str) -> None:
    """Runtime guard that converts validation errors into an HTTP-safe exception."""
    try:
        validate_public_http_endpoint(endpoint)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
