from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query

from backend.app.search.service import get_opensearch_client, search_records

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(
    q: str = Query(default="", max_length=300),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    repository_id: int | None = Query(default=None, ge=1),
    resource_type: str | None = Query(default=None, max_length=255),
    from_year: int | None = Query(default=None, ge=1000, le=9999),
    until_year: int | None = Query(default=None, ge=1000, le=9999),
    sort: Literal["relevance", "newest", "oldest"] = "relevance",
):
    if from_year and until_year and from_year > until_year:
        raise HTTPException(status_code=422, detail="from_year cannot be later than until_year.")
    try:
        return search_records(
            get_opensearch_client(),
            query=q,
            page=page,
            page_size=page_size,
            repository_id=repository_id,
            resource_type=resource_type,
            from_year=from_year,
            until_year=until_year,
            sort=sort,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Search service is temporarily unavailable.") from exc
