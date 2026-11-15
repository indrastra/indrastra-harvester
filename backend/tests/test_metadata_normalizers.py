import pytest
from defusedxml.common import DefusedXmlException

from backend.app.metadata.normalizers import normalize_metadata


OAI_DC_RECORD = """<record xmlns:oai="http://www.openarchives.org/OAI/2.0/"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">
 <header><identifier>oai:repo:42</identifier></header>
 <metadata><oai_dc:dc>
  <dc:title>  A Scholarly   Article </dc:title>
  <dc:creator>Jane Doe</dc:creator>
  <dc:subject>Open science</dc:subject>
  <dc:date>2026-05-01</dc:date>
  <dc:identifier>https://doi.org/10.1234/example</dc:identifier>
 </oai_dc:dc></metadata>
</record>"""


DATACITE_RECORD = """<record xmlns:d="http://datacite.org/schema/kernel-4">
 <metadata><d:resource>
  <d:identifier identifierType="DOI">10.5555/12345</d:identifier>
  <d:creators><d:creator><d:creatorName>Alex Researcher</d:creatorName></d:creator></d:creators>
  <d:titles><d:title>Dataset Title</d:title></d:titles>
  <d:publisher>Example University</d:publisher>
  <d:publicationYear>2025</d:publicationYear>
  <d:resourceType resourceTypeGeneral="Dataset">Dataset</d:resourceType>
 </d:resource></metadata>
</record>"""


def test_oai_dc_crosswalk_normalizes_fields_and_excludes_oai_header():
    result = normalize_metadata(OAI_DC_RECORD, "oai_dc")
    assert result.title == ["A Scholarly Article"]
    assert result.creators == ["Jane Doe"]
    assert result.subjects == ["Open science"]
    assert result.publication_dates == ["2026-05-01"]
    assert result.identifiers == ["https://doi.org/10.1234/example"]
    assert "oai:repo:42" not in result.identifiers
    assert result.normalization_version == "1.0.0"


def test_datacite_crosswalk_normalizes_common_resource_fields():
    result = normalize_metadata(DATACITE_RECORD, "datacite")
    assert result.title == ["Dataset Title"]
    assert result.creators == ["Alex Researcher"]
    assert result.publishers == ["Example University"]
    assert result.publication_dates == ["2025"]
    assert result.resource_types == ["Dataset"]


def test_unknown_schema_is_preserved_without_guessing_a_full_crosswalk():
    xml = "<record><metadata><custom><title>Custom title</title><identifier>ID-7</identifier></custom></metadata></record>"
    result = normalize_metadata(xml, "custom_format")
    assert result.schema == "custom_format"
    assert result.title == ["Custom title"]
    assert result.identifiers == ["ID-7"]
    assert result.raw_fields["title"] == ["Custom title"]


def test_xml_external_entities_are_rejected():
    xml = """<!DOCTYPE x [<!ENTITY ext SYSTEM "file:///etc/passwd">]>
    <record><metadata><dc><title>&ext;</title></dc></metadata></record>"""
    with pytest.raises(DefusedXmlException):
        normalize_metadata(xml, "oai_dc")
