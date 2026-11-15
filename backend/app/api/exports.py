from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.exports.service import serialize_csv, serialize_xml
from backend.app.harvest.models import SourceRecord
from backend.app.metadata.models import NormalizedRecord
from backend.app.repositories.models import Repository
from backend.app.search.service import INDEX_NAME, ensure_index, get_opensearch_client

router = APIRouter(prefix="/exports", tags=["exports"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def _export_search(
    client,
    *,
    query: str,
    repository_id: int | None,
    resource_type: str | None,
    from_year: int | None,
    until_year: int | None,
    page: int,
    limit: int,
    sort: str,
):
    ensure_index(client)
    filters = []
    if repository_id is not None:
        filters.append({"term": {"repository_id": repository_id}})
    if resource_type:
        filters.append({"term": {"resource_types": resource_type}})
    year_range = {}
    if from_year is not None:
        year_range["gte"] = from_year
    if until_year is not None:
        year_range["lte"] = until_year
    if year_range:
        filters.append({"range": {"publication_year": year_range}})

    must = [{"match_all": {}}]
    if query.strip():
        must = [{
            "simple_query_string": {
                "query": query,
                "fields": ["title^5", "creators^3", "subjects^2", "descriptions", "identifiers", "publishers"],
                "default_operator": "and",
                "flags": "OR|AND|PREFIX|PHRASE",
            }
        }]
    if sort == "newest":
        sort_order = [{"publication_year": {"order": "desc", "missing": "_last"}}, {"_score": "desc"}]
    elif sort == "oldest":
        sort_order = [{"publication_year": {"order": "asc", "missing": "_last"}}, {"_score": "desc"}]
    else:
        sort_order = ["_score", {"publication_year": {"order": "desc", "missing": "_last"}}]

    result = client.search(
        index=INDEX_NAME,
        body={
            "query": {"bool": {"must": must, "filter": filters}},
            "from": (page - 1) * limit,
            "size": limit,
            "sort": sort_order,
            "track_total_hits": True,
        },
    )
    hits = result.get("hits", {})
    total = hits.get("total", 0)
    total_value = total.get("value", 0) if isinstance(total, dict) else total
    ids = [int(hit["_source"]["source_record_id"]) for hit in hits.get("hits", [])]
    return ids, total_value


@router.get("")
def export_records(
    db: DatabaseSession,
    format: Literal["json", "csv", "xml", "oai_dc"] = "json",
    q: str = Query(default="", max_length=300),
    repository_id: int | None = Query(default=None, ge=1),
    resource_type: str | None = Query(default=None, max_length=255),
    from_year: int | None = Query(default=None, ge=1000, le=9999),
    until_year: int | None = Query(default=None, ge=1000, le=9999),
    page: int = Query(default=1, ge=1, le=1000),
    limit: int = Query(default=100, ge=1, le=1000),
    sort: Literal["relevance", "newest", "oldest"] = "relevance",
):
    if from_year and until_year and from_year > until_year:
        raise HTTPException(status_code=422, detail="from_year cannot be later than until_year.")
    if (page - 1) * limit > 9000:
        raise HTTPException(status_code=422, detail="Export offset exceeds the search index result window.")

    try:
        ids, total = _export_search(
            get_opensearch_client(),
            query=q,
            repository_id=repository_id,
            resource_type=resource_type,
            from_year=from_year,
            until_year=until_year,
            page=page,
            limit=limit,
            sort=sort,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Search service is temporarily unavailable.") from exc

    if not ids:
        records = []
    else:
        rows = db.execute(
            select(NormalizedRecord, SourceRecord, Repository)
            .join(SourceRecord, SourceRecord.id == NormalizedRecord.source_record_id)
            .join(Repository, Repository.id == SourceRecord.repository_id)
            .where(
                NormalizedRecord.source_record_id.in_(ids),
                NormalizedRecord.is_deleted.is_(False),
                SourceRecord.is_deleted.is_(False),
                Repository.is_enabled.is_(True),
            )
        ).all()
        by_id = {}
        for normalized, source, repository in rows:
            by_id[source.id] = {
                "id": source.id,
                "repository_id": repository.id,
                "repository_name": repository.name,
                "oai_identifier": source.oai_identifier,
                "metadata_prefix": source.metadata_prefix,
                "datestamp": source.datestamp,
                "metadata": normalized.data,
            }
        records = [by_id[record_id] for record_id in ids if record_id in by_id]

    headers = {
        "X-Total-Hits": str(total),
        "X-Exported-Records": str(len(records)),
        "Content-Disposition": f'attachment; filename="indrastra-harvester-{format}-export.{ "json" if format == "json" else "csv" if format == "csv" else "xml" }"',
    }
    if format == "json":
        return Response(
            content=__import__("json").dumps(
                jsonable_encoder({"total_hits": total, "exported": len(records), "records": records}),
                ensure_ascii=False,
            ),
            media_type="application/json",
            headers=headers,
        )
    if format == "csv":
        return Response(content=serialize_csv(records), media_type="text/csv; charset=utf-8", headers=headers)
    return Response(
        content=serialize_xml(records, oai_dc=format == "oai_dc"),
        media_type="application/xml; charset=utf-8",
        headers=headers,
    )
