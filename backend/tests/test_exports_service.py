import csv
import xml.etree.ElementTree as ET

from backend.app.exports.service import serialize_csv, serialize_xml


SAMPLE_RECORD = {
    "id": 42,
    "repository_id": 7,
    "repository_name": "Example Repository",
    "oai_identifier": "oai:example:42",
    "metadata_prefix": "oai_dc",
    "metadata": {
        "title": ["A Research Article"],
        "creators": ["Jane Doe"],
        "subjects": ["Open science"],
        "identifiers": ["https://doi.org/10.1234/example"],
        "rights": ["CC BY 4.0"],
    },
}


def test_csv_export_contains_source_identity_and_repeated_metadata():
    output = serialize_csv([SAMPLE_RECORD])
    rows = list(csv.DictReader(output.splitlines()))
    assert len(rows) == 1
    assert rows[0]["oai_identifier"] == "oai:example:42"
    assert rows[0]["title"] == "A Research Article"
    assert rows[0]["creators"] == "Jane Doe"


def test_oai_dc_xml_export_uses_correct_dc_element_namespaces():
    output = serialize_xml([SAMPLE_RECORD], oai_dc=True)
    root = ET.fromstring(output)
    dc_root = root.find(".//{http://www.openarchives.org/OAI/2.0/oai_dc/}dc")
    assert dc_root is not None
    title = dc_root.find("{http://purl.org/dc/elements/1.1/}title")
    creator = dc_root.find("{http://purl.org/dc/elements/1.1/}creator")
    rights = dc_root.find("{http://purl.org/dc/elements/1.1/}rights")
    assert title is not None and title.text == "A Research Article"
    assert creator is not None and creator.text == "Jane Doe"
    assert rights is not None and rights.text == "CC BY 4.0"


def test_canonical_xml_export_escapes_metadata_values():
    record = {**SAMPLE_RECORD, "metadata": {"title": ["A < B & C"]}}
    output = serialize_xml([record])
    root = ET.fromstring(output)
    title = root.find(".//title")
    assert title is not None and title.text == "A < B & C"
