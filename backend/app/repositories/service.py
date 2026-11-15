from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.harvest.exceptions import OAIError
from backend.app.harvest.oai_client import NS, OAIPMHClient
from backend.app.repositories.models import Repository
from backend.app.repositories.security import validate_public_http_endpoint


class RepositoryAlreadyExistsError(ValueError):
    pass


class RepositoryValidationError(ValueError):
    pass


def validate_repository_endpoint(endpoint: str) -> dict:
    """Validate the public endpoint and discover basic OAI-PMH capabilities."""
    safe_endpoint = validate_public_http_endpoint(endpoint)
    # The deployment egress firewall/proxy must also enforce the destination policy.
    validate_public_http_endpoint(safe_endpoint)

    try:
        with OAIPMHClient(safe_endpoint) as client:
            identify = client.identify()
            identify_node = identify.root.find("oai:Identify", NS)
            if identify_node is None:
                raise RepositoryValidationError("Identify response has no Identify element.")

            def read_text(tag: str) -> str | None:
                node = identify_node.find(f"oai:{tag}", NS)
                return (node.text or "").strip() if node is not None else None

            formats: list[dict[str, str]] = []
            sets: list[dict[str, str]] = []
            try:
                format_response = client.list_metadata_formats()
                format_root = format_response.root.find("oai:ListMetadataFormats", NS)
                if format_root is not None:
                    for item in format_root.findall("oai:metadataFormat", NS):
                        formats.append({
                            "metadata_prefix": _child_text(item, "metadataPrefix"),
                            "schema": _child_text(item, "schema"),
                            "metadata_namespace": _child_text(item, "metadataNamespace"),
                        })
            except OAIError:
                formats = []

            try:
                set_response = client.list_sets()
                set_root = set_response.root.find("oai:ListSets", NS)
                if set_root is not None:
                    for item in set_root.findall("oai:set", NS):
                        sets.append({
                            "set_spec": _child_text(item, "setSpec"),
                            "set_name": _child_text(item, "setName"),
                        })
            except OAIError:
                sets = []

            return {
                "oai_repository_name": read_text("repositoryName"),
                "admin_email": read_text("adminEmail"),
                "earliest_datestamp": read_text("earliestDatestamp"),
                "deleted_record": read_text("deletedRecord"),
                "granularity": read_text("granularity"),
                "metadata_formats": [item for item in formats if item["metadata_prefix"]],
                "sets": [item for item in sets if item["set_spec"]],
                "last_validated_at": datetime.now(UTC),
            }
    except OAIError as exc:
        raise RepositoryValidationError(str(exc)) from exc


def create_repository(db: Session, values: dict) -> Repository:
    values = dict(values)
    endpoint = validate_public_http_endpoint(values.pop("endpoint"))
    validate_endpoint = values.pop("validate_endpoint", True)

    existing = db.scalar(select(Repository).where(Repository.endpoint == endpoint))
    if existing:
        raise RepositoryAlreadyExistsError("A repository with this endpoint already exists.")

    validation = validate_repository_endpoint(endpoint) if validate_endpoint else {}
    repository = Repository(
        **values,
        endpoint=endpoint,
        validation_status="valid" if validation else "pending",
        **validation,
    )
    db.add(repository)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise RepositoryAlreadyExistsError(
            "A repository with this endpoint already exists."
        ) from exc
    db.refresh(repository)
    return repository


def refresh_repository_validation(db: Session, repository: Repository) -> Repository:
    try:
        validation = validate_repository_endpoint(repository.endpoint)
    except RepositoryValidationError as exc:
        repository.validation_status = "failed"
        repository.last_validation_error = str(exc)[:4000]
        repository.last_validated_at = datetime.now(UTC)
        db.commit()
        db.refresh(repository)
        raise

    for key, value in validation.items():
        setattr(repository, key, value)
    repository.validation_status = "valid"
    repository.last_validation_error = None
    db.commit()
    db.refresh(repository)
    return repository


def _child_text(parent, tag: str) -> str:
    node = parent.find(f"oai:{tag}", NS)
    return (node.text or "").strip() if node is not None else ""
