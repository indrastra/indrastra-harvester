import httpx
import pytest

from backend.app.harvest.exceptions import (
    OAIParseError,
    OAIProtocolError,
    OAIRequestError,
)
from backend.app.harvest.oai_client import OAIPMHClient, OAI_NS

OAI = f'xmlns="{OAI_NS}"'


def response(body: str) -> httpx.Response:
    return httpx.Response(200, text=body, request=httpx.Request("GET", "https://repo.example/oai"))


def test_identify_parses_protocol_response():
    body = f"""<OAI-PMH {OAI}>
      <responseDate>2026-11-15T10:00:00Z</responseDate>
      <request verb="Identify">https://repo.example/oai</request>
      <Identify><repositoryName>Example Repository</repositoryName></Identify>
    </OAI-PMH>"""
    client = OAIPMHClient("https://repo.example/oai", client=httpx.Client(
        transport=httpx.MockTransport(lambda request: response(body))
    ))
    result = client.identify()
    assert result.verb == "Identify"
    assert result.response_date == "2026-11-15T10:00:00Z"


def test_protocol_error_is_raised():
    body = f"""<OAI-PMH {OAI}>
      <responseDate>2026-11-15T10:00:00Z</responseDate>
      <request verb="ListRecords">https://repo.example/oai</request>
      <error code="noRecordsMatch">No records found</error>
    </OAI-PMH>"""
    client = OAIPMHClient("https://repo.example/oai", client=httpx.Client(
        transport=httpx.MockTransport(lambda request: response(body))
    ))
    with pytest.raises(OAIProtocolError, match="noRecordsMatch"):
        client.list_records("oai_dc")


def test_invalid_endpoint_rejected():
    with pytest.raises(OAIRequestError):
        OAIPMHClient("file:///etc/passwd")


def test_invalid_xml_rejected():
    client = OAIPMHClient("https://repo.example/oai", client=httpx.Client(
        transport=httpx.MockTransport(lambda request: response("<broken"))
    ))
    with pytest.raises(OAIParseError):
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

    client = OAIPMHClient(
        "https://repo.example/oai",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    records = list(client.iter_records("oai_dc"))
    assert len(records) == 2
    assert seen_requests[1] == {"verb": "ListRecords", "resumptionToken": "next-page-token"}
