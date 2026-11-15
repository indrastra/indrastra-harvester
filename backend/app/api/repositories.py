from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.dependencies import require_admin
from backend.app.db.session import get_db
from backend.app.repositories.models import Repository
from backend.app.repositories.schemas import RepositoryCreate, RepositoryRead, RepositoryUpdate
from backend.app.repositories.service import (
    RepositoryAlreadyExistsError,
    RepositoryValidationError,
    create_repository,
    refresh_repository_validation,
)

router = APIRouter(prefix="/repositories", tags=["repositories"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def register_repository(payload: RepositoryCreate, db: DatabaseSession):
    try:
        return create_repository(db, payload.model_dump())
    except RepositoryAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RepositoryValidationError as exc:
        raise HTTPException(status_code=422, detail=f"OAI-PMH validation failed: {exc}") from exc


@router.get("", response_model=list[RepositoryRead])
def list_repositories(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: DatabaseSession,
):
    statement = select(Repository).order_by(Repository.id).offset(offset).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/{repository_id}", response_model=RepositoryRead)
def get_repository(repository_id: int, db: DatabaseSession):
    repository = db.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return repository


@router.patch(
    "/{repository_id}", response_model=RepositoryRead,
    dependencies=[Depends(require_admin)],
)
def update_repository(
    repository_id: int, payload: RepositoryUpdate, db: DatabaseSession
):
    repository = db.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(repository, key, value)
    db.commit()
    db.refresh(repository)
    return repository


@router.post(
    "/{repository_id}/validate", response_model=RepositoryRead,
    dependencies=[Depends(require_admin)],
)
def validate_repository(repository_id: int, db: DatabaseSession):
    repository = db.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
    try:
        return refresh_repository_validation(db, repository)
    except RepositoryValidationError as exc:
        raise HTTPException(status_code=422, detail=f"OAI-PMH validation failed: {exc}") from exc


@router.delete(
    "/{repository_id}", status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_repository(repository_id: int, db: DatabaseSession):
    repository = db.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
    repository.is_enabled = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
