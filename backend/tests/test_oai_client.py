import httpx
import pytest

from backend.app.harvest.exceptions import (
    OAIParseError,
    OAIProtocolError,
    OAIRequestError,
)
from backend.app.harvest.oai_client import OAI_NS, OAIPMHClient

OAI = f'xmlns="{OAI_NS}"'


def response(body: str) -> httpx.Response:
    return httpx.Response(
        200, text=body,
        request=httpx.Request("GET", "https://repo.example/oai"),
    )


def make_client(handler, **kwargs):
    return OAIPMHClient(
        "https://repo.example/oai",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        **kwargs,
    )


def test_identify_parses_protocol_response():
    body = f"""<OAI-PMH {OAI}>
      <responseDate>2026-11-15T10:00:00Z</responseDate>
      <request verb="Identify">https://repo.example/oai</request>
      <Identify><repositoryName>Example Repository</repositoryName></Identify>
    </OAI-PMH>"""
    result = make_client(lambda request: response(body)).identify()
    assert result.verb == "Identify"
    assert result.response_date == "2026-11-15T10:00:00Z"


def test_protocol_error_is_raised():
    body = f"""<OAI-PMH {OAI}>
      <responseDate>2026-11-15T10:00:00Z</responseDate>
      <request verb="ListRecords">https://repo.example/oai</request>
      <error code="noRecordsMatch">No records found</error>
    </OAI-PMH>"""
    client = make_client(lambda request: response(body))
    with pytest.raises(OAIProtocolError, match="noRecordsMatch"):
        client.list_records("oai_dc")


def test_invalid_endpoint_rejected():
    with pytest.raises(OAIRequestError):
        OAIPMHClient("file:///etc/passwd")


def test_invalid_xml_rejected():
    client = make_client(lambda request: response("<broken"))
    with pytest.raises(OAIParseError):
        client.identify()


def test_xml_dtd_and_entity_expansion_rejected():
    body = """<?xml version="1.0"?>
    <!DOCTYPE OAI-PMH [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
    <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
      <responseDate>2026-11-15T10:00:00Z</responseDate>
      <request verb="Identify">https://repo.example/oai</request>
      <Identify><repositoryName>&xxe;</repositoryName></Identify>
    </OAI-PMH>"""
    client = make_client(lambda request: response(body))
    with pytest.raises(OAIParseError, match="unsafe XML"):
        client.identify()


def test_response_size_limit_is_enforced_while_streaming():
    body = f"""<OAI-PMH {OAI}><responseDate>2026-11-15T10:00:00Z</responseDate>
    <request verb="Identify">https://repo.example/oai</request>
    <Identify><repositoryName>Example Repository</repositoryName></Identify></OAI-PMH>"""
    client = make_client(lambda request: response(body), max_response_bytes=20)
    with pytest.raises(Exception, match="response exceeds configured size limit"):
        client.identify()


def test_resumption_token_pagination():
    page_one = f"""<OAI-PMH {OAI}>
      <responseDate>2026-11-15T10:00:00Z</responseDate>
      <request verb="ListRecords">https://repo.example/oai</request>
      <ListRecords>
        <record><header><identifier>oai:repo:1</identifier></header></record>
        <resumptionToken cursor="0">next-page-token</resumptionToken>
      </ListRecords>
    </OAI-PMH>"""
    page_two = f"""<OAI-PMH {OAI}>
      <responseDate>2026-11-15T10:01:00Z</responseDate>
      <request verb="ListRecords">https://repo.example/oai</request>
      <ListRecords>
        <record><header><identifier>oai:repo:2</identifier></header></record>
        <resumptionToken cursor="1"></resumptionToken>
      </ListRecords>
    </OAI-PMH>"""
    seen_requests = []

    def handler(request):
        seen_requests.append(dict(request.url.params))
        return response(page_one if len(seen_requests) == 1 else page_two)

    client = make_client(handler)
    records = list(client.iter_records("oai_dc"))
    assert len(records) == 2
    assert seen_requests[1] == {
        "verb": "ListRecords",
        "resumptionToken": "next-page-token",
    }
