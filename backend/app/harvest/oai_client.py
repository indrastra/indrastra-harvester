"""Minimal, defensive OAI-PMH 2.0 client.

The client supports all six OAI-PMH verbs and resumption-token pagination.
XML parsing rejects DTD/entity declarations, and response bytes are bounded
while streaming rather than after buffering the full body.
"""
from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Self
from urllib.parse import urlparse

import httpx
from defusedxml import ElementTree as SafeET
from defusedxml.common import DefusedXmlException

from .exceptions import (
    OAIParseError,
    OAIProtocolError,
    OAIRequestError,
    OAITransportError,
)

OAI_NS = "http://www.openarchives.org/OAI/2.0/"
NS = {"oai": OAI_NS}
VALID_VERBS = {
    "Identify", "ListMetadataFormats", "ListSets",
    "ListIdentifiers", "ListRecords", "GetRecord",
}


@dataclass(frozen=True)
class OAIResponse:
    """Parsed protocol response."""

    root: ET.Element
    verb: str
    request_url: str
    response_date: str | None

    @property
    def errors(self) -> list[tuple[str, str]]:
        return [
            (node.attrib.get("code", "unknown"), (node.text or "").strip())
            for node in self.root.findall("oai:error", NS)
        ]

    def raise_for_protocol_errors(self) -> None:
        if self.errors:
            code, message = self.errors[0]
            raise OAIProtocolError(f"{code}: {message}")


class OAIPMHClient:
    """OAI-PMH 2.0 HTTP client."""

    def __init__(
        self,
        endpoint: str,
        timeout: float = 30.0,
        user_agent: str = "IndraStra-Harvester/0.1",
        max_response_bytes: int = 20_000_000,
        client: httpx.Client | None = None,
    ) -> None:
        parsed = urlparse(endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise OAIRequestError("Endpoint must be an absolute HTTP or HTTPS URL.")
        if parsed.username or parsed.password:
            raise OAIRequestError("Credentials in repository endpoint URLs are not allowed.")
        if max_response_bytes < 1:
            raise OAIRequestError("max_response_bytes must be positive.")

        self.endpoint = endpoint
        self.timeout = timeout
        self.max_response_bytes = max_response_bytes
        self._owns_client = client is None
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": user_agent, "Accept": "application/xml, text/xml"},
            follow_redirects=False,
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def request(self, verb: str, **params: str) -> OAIResponse:
        if verb not in VALID_VERBS:
            raise OAIRequestError(f"Unsupported OAI-PMH verb: {verb}")
        if "verb" in params:
            raise OAIRequestError("The verb parameter must not be supplied twice.")

        query = {"verb": verb, **params}
        try:
            with self.client.stream(
                "GET", self.endpoint, params=query, timeout=self.timeout
            ) as response:
                if response.is_redirect:
                    raise OAITransportError(
                        "Repository redirects are not followed automatically."
                    )
                if response.status_code >= 400:
                    raise OAITransportError(
                        f"Repository returned HTTP {response.status_code}."
                    )

                chunks: list[bytes] = []
                total_bytes = 0
                for chunk in response.iter_bytes():
                    total_bytes += len(chunk)
                    if total_bytes > self.max_response_bytes:
                        raise OAITransportError(
                            "Repository response exceeds configured size limit."
                        )
                    chunks.append(chunk)
                content = b"".join(chunks)
        except OAITransportError:
            raise
        except httpx.TimeoutException as exc:
            raise OAITransportError(f"Repository request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise OAITransportError(f"Repository request failed: {exc}") from exc

        try:
            root = SafeET.fromstring(content)
        except (ET.ParseError, DefusedXmlException) as exc:
            raise OAIParseError(f"Repository returned malformed or unsafe XML: {exc}") from exc

        if root.tag != f"{{{OAI_NS}}}OAI-PMH":
            raise OAIParseError("Response root is not an OAI-PMH element.")

        response_verb = next(
            (child.tag.rsplit("}", 1)[-1] for child in root if child.tag.endswith(verb)),
            verb,
        )
        response_date_node = root.find("oai:responseDate", NS)
        request_node = root.find("oai:request", NS)
        result = OAIResponse(
            root=root,
            verb=response_verb,
            request_url=(request_node.text or "").strip()
            if request_node is not None else self.endpoint,
            response_date=(response_date_node.text or "").strip()
            if response_date_node is not None else None,
        )
        result.raise_for_protocol_errors()
        return result

    def identify(self) -> OAIResponse:
        return self.request("Identify")

    def list_metadata_formats(self, identifier: str | None = None) -> OAIResponse:
        params = {"identifier": identifier} if identifier else {}
        return self.request("ListMetadataFormats", **params)

    def list_sets(self) -> OAIResponse:
        return self.request("ListSets")

    def list_identifiers(
        self, metadata_prefix: str, *, from_: str | None = None,
        until: str | None = None, set_: str | None = None,
    ) -> OAIResponse:
        return self.request(
            "ListIdentifiers",
            **_optional_params(
                metadataPrefix=metadata_prefix,
                **{"from": from_, "until": until, "set": set_},
            ),
        )

    def list_records(
        self, metadata_prefix: str, *, from_: str | None = None,
        until: str | None = None, set_: str | None = None,
    ) -> OAIResponse:
        return self.request(
            "ListRecords",
            **_optional_params(
                metadataPrefix=metadata_prefix,
                **{"from": from_, "until": until, "set": set_},
            ),
        )

    def get_record(self, identifier: str, metadata_prefix: str) -> OAIResponse:
        return self.request(
            "GetRecord", identifier=identifier, metadataPrefix=metadata_prefix
        )

    def iter_records(
        self, metadata_prefix: str, *, from_: str | None = None,
        until: str | None = None, set_: str | None = None,
        pause_seconds: float = 0.0,
    ) -> Iterator[ET.Element]:
        """Yield record elements across all ListRecords pages."""
        response = self.list_records(
            metadata_prefix, from_=from_, until=until, set_=set_
        )
        while True:
            records = response.root.find("oai:ListRecords", NS)
            if records is None:
                raise OAIParseError("ListRecords response has no ListRecords element.")
            yield from records.findall("oai:record", NS)

            token_node = records.find("oai:resumptionToken", NS)
            token = (token_node.text or "").strip() if token_node is not None else ""
            if not token:
                break
            if pause_seconds > 0:
                time.sleep(pause_seconds)
            response = self.request("ListRecords", resumptionToken=token)


def _optional_params(**params: str | None) -> dict[str, str]:
    return {key: value for key, value in params.items() if value is not None}
