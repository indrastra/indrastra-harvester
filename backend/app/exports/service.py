import csv
import io
import xml.etree.ElementTree as ET
from typing import Any


CSV_FIELDS = [
    "id", "repository_id", "repository_name", "oai_identifier", "metadata_prefix",
    "title", "creators", "contributors", "subjects", "descriptions", "publishers",
    "publication_dates", "resource_types", "formats", "identifiers", "languages",
    "relations", "sources", "rights", "coverages",
]

DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
OAI_DC_NAMESPACE = "http://www.openarchives.org/OAI/2.0/oai_dc/"
OAI_DC_ELEMENTS = {
    "title": "title",
    "creators": "creator",
    "contributors": "contributor",
    "subjects": "subject",
    "descriptions": "description",
    "publishers": "publisher",
    "publication_dates": "date",
    "resource_types": "type",
    "formats": "format",
    "identifiers": "identifier",
    "languages": "language",
    "relations": "relation",
    "sources": "source",
    "rights": "rights",
    "coverages": "coverage",
}
ET.register_namespace("dc", DC_NAMESPACE)
ET.register_namespace("oai_dc", OAI_DC_NAMESPACE)


def serialize_csv(records: list[dict[str, Any]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for record in records:
        metadata = record.get("metadata", {})
        row: dict[str, Any] = {
            "id": record.get("id"),
            "repository_id": record.get("repository_id"),
            "repository_name": record.get("repository_name"),
            "oai_identifier": record.get("oai_identifier"),
            "metadata_prefix": record.get("metadata_prefix"),
        }
        for field in CSV_FIELDS[5:]:
            values = metadata.get(field, [])
            row[field] = " | ".join(str(value) for value in values) if isinstance(values, list) else values
        writer.writerow(row)
    return output.getvalue()


def serialize_xml(records: list[dict[str, Any]], *, oai_dc: bool = False) -> str:
    root = ET.Element("records", {"count": str(len(records))})
    for record in records:
        node = ET.SubElement(root, "record", {
            "id": str(record.get("id", "")),
            "repository_id": str(record.get("repository_id", "")),
            "oai_identifier": str(record.get("oai_identifier", "")),
        })
        metadata = record.get("metadata", {})
        if oai_dc:
            dc_root = ET.SubElement(node, f"{{{OAI_DC_NAMESPACE}}}dc")
            for key, element_name in OAI_DC_ELEMENTS.items():
                values = metadata.get(key, [])
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    element = ET.SubElement(dc_root, f"{{{DC_NAMESPACE}}}{element_name}")
                    element.text = str(value)
        else:
            metadata_node = ET.SubElement(node, "metadata")
            for key, values in metadata.items():
                if key == "raw_fields":
                    continue
                if not isinstance(values, list):
                    values = [values]
                for value in values:
                    element = ET.SubElement(metadata_node, key.replace("_", "-"))
                    element.text = str(value)
    return ET.tostring(root, encoding="unicode", xml_declaration=True)
