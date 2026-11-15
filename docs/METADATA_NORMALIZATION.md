# Metadata normalization and crosswalks

## Design

Source XML is the immutable evidence layer. Normalized metadata is a derived projection used by search, exports, and analytics. Every normalized row records the source record, repository, OAI identifier, source metadata prefix, and normalization version.

The first crosswalk release supports:

| OAI metadataPrefix | Crosswalk | Notes |
|---|---|---|
| `oai_dc` | Qualified local-name mapping for the 15 Dublin Core elements | Extracts values from the metadata payload, not the OAI header |
| `datacite` | Initial DataCite XML mapping | Covers titles, creators, contributors, subjects, descriptions, publisher, year, resource type, identifiers, relations, rights, and selected coverage |
| Other prefixes | Generic XML field map | Preserves local-name fields and maps only common title, creator, description, and identifier fields |

## Canonical fields

- title and alternate titles
- creators and contributors
- subjects and descriptions
- publishers and publication dates
- resource types and formats
- identifiers and languages
- relations and sources
- rights and coverage
- raw local-name field map

Fields remain arrays when a source can supply repeated values. The source's original XML remains unchanged and is not discarded when a crosswalk cannot interpret a field.

## Provenance and versioning

A source record is identified by `repository_id + oai_identifier`. Each changed source payload creates an immutable `source_record_versions` snapshot. The current `normalized_records` row is a rebuildable projection keyed by `source_record_id`. Deleted OAI headers mark the normalized projection as deleted while retaining all source versions.

## Safety and limitations

XML is parsed with defusedxml. External entities are rejected. Crosswalks use local element names to accommodate namespace URI variations; they do not claim full semantic equivalence between all repository schemas. Unknown fields remain in `raw_fields`.

The DataCite crosswalk is an initial subset, not a full implementation of every DataCite kernel version or property. Qualified Dublin Core, MODS, MARCXML, and JATS require dedicated future adapters and fixture suites.

## Extending the registry

Add a pure normalizer returning `NormalizedMetadata`, register it in `NORMALIZERS` using the repository's metadataPrefix, and add representative fixtures for namespace variations, repeated fields, empty values, malformed XML, and hostile entity declarations. Bump `normalization_version` whenever the meaning or structure of the canonical projection changes.
