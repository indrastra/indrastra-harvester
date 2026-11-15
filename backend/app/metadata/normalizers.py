"""Deterministic, versioned metadata crosswalks for harvested source XML."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any
from xml.etree.ElementTree import Element

from defusedxml import ElementTree as SafeET


@dataclass(slots=True)
class NormalizedMetadata:
    schema: str
    normalization_version: str = "1.0.0"
    title: list[str] = field(default_factory=list)
    creators: list[str] = field(default_factory=list)
    contributors: list[str] = field(default_factory=list)
    subjects: list[str] = field(default_factory=list)
    descriptions: list[str] = field(default_factory=list)
    publishers: list[str] = field(default_factory=list)
    publication_dates: list[str] = field(default_factory=list)
    resource_types: list[str] = field(default_factory=list)
    formats: list[str] = field(default_factory=list)
    identifiers: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    relations: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    rights: list[str] = field(default_factory=list)
    coverages: list[str] = field(default_factory=list)
    alternate_titles: list[str] = field(default_factory=list)
    raw_fields: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].split(":")[-1].casefold()


def _values(root: Element) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    for node in root.iter():
        if node is root:
            continue
        value = " ".join("".join(node.itertext()).split())
        if not value:
            continue
        key = _local_name(node.tag)
        fields.setdefault(key, []).append(value)
    return fields


def _map_fields(fields: dict[str, list[str]], mapping: dict[str, str], schema: str) -> NormalizedMetadata:
    result = NormalizedMetadata(schema=schema, raw_fields=fields)
    for source, target in mapping.items():
        if source in fields:
            setattr(result, target, list(dict.fromkeys(fields[source])))
    return result


DC_MAPPING = {
    "title": "title",
    "creator": "creators",
    "contributor": "contributors",
    "subject": "subjects",
    "description": "descriptions",
    "publisher": "publishers",
    "date": "publication_dates",
    "type": "resource_types",
    "format": "formats",
    "identifier": "identifiers",
    "language": "languages",
    "relation": "relations",
    "source": "sources",
    "rights": "rights",
    "coverage": "coverages",
}
DATACITE_MAPPING = {
    "title": "title",
    "creatorname": "creators",
    "contributorname": "contributors",
    "subject": "subjects",
    "description": "descriptions",
    "publisher": "publishers",
    "publicationyear": "publication_dates",
    "resourcetype": "resource_types",
    "format": "formats",
    "identifier": "identifiers",
    "language": "languages",
    "relatedidentifier": "relations",
    "rights": "rights",
    "geoLocationPlace": "coverages",
}


def normalize_oai_dc(xml: str) -> NormalizedMetadata:
    root = SafeET.fromstring(xml)
    return _map_fields(_values(root), DC_MAPPING, "oai_dc")


def normalize_datacite(xml: str) -> NormalizedMetadata:
    root = SafeET.fromstring(xml)
    return _map_fields(_values(root), DATACITE_MAPPING, "datacite")


def normalize_generic_xml(xml: str, schema: str) -> NormalizedMetadata:
    """Retain unknown schemas as a safe local-name field map without guessing crosswalks."""
    root = SafeET.fromstring(xml)
    fields = _values(root)
    result = NormalizedMetadata(schema=schema or "unknown", raw_fields=fields)
    if "title" in fields:
        result.title = fields["title"]
    if "identifier" in fields:
        result.identifiers = fields["identifier"]
    if "creator" in fields:
        result.creators = fields["creator"]
    if "description" in fields:
        result.descriptions = fields["description"]
    return result


Normalizer = Callable[[str], NormalizedMetadata]
NORMALIZERS: dict[str, Normalizer] = {
    "oai_dc": normalize_oai_dc,
    "datacite": normalize_datacite,
}


def normalize_metadata(xml: str, metadata_prefix: str) -> NormalizedMetadata:
    """Apply a registered crosswalk, otherwise preserve generic source fields."""
    normalizer = NORMALIZERS.get(metadata_prefix.casefold())
    if normalizer is not None:
        return normalizer(xml)
    return normalize_generic_xml(xml, metadata_prefix)
