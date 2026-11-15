from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_user, require_admin
from backend.app.db.session import get_db
from backend.app.users.models import AuditEvent, Role, User
from backend.app.users.security import create_access_token, hash_password, jwt_secret, verify_password

DUMMY_PASSWORD_HASH = hash_password("indrastra-dummy-login-password")

router = APIRouter(prefix="/auth", tags=["authentication"])
DatabaseSession = Annotated[Session, Depends(get_db)]


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class UserCreate(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    full_name: str = Field(default="", max_length=255)
    password: str = Field(min_length=12, max_length=256)
    roles: list[str] = Field(default_factory=lambda: ["viewer"], min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("A valid email address is required.")
        return normalized


class RolesUpdate(BaseModel):
    roles: list[str] = Field(min_length=1)


class ActiveUpdate(BaseModel):
    is_active: bool


def ensure_default_roles(db: Session) -> None:
    defaults = {
        "admin": "Full administrative access.",
        "harvester": "Repository and harvesting operations.",
        "viewer": "Read-only access to protected operational views.",
    }
    existing = set(db.scalars(select(Role.name)).all())
    for name, description in defaults.items():
        if name not in existing:
            db.add(Role(name=name, description=description))
    db.flush()


def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "roles": sorted(role.name for role in user.roles),
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }


@router.post("/token")
def issue_token(payload: LoginRequest, db: DatabaseSession):
    try:
        jwt_secret()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    user = db.scalar(select(User).where(func.lower(User.email) == payload.email.strip().lower()))
    now = datetime.now(UTC)
    if user is None:
        verify_password(payload.password, DUMMY_PASSWORD_HASH)
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if user.locked_until is not None and user.locked_until > now:
        raise HTTPException(status_code=429, detail="Login temporarily locked. Try again later.")
    if not user.is_active or not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.failed_login_attempts = 0
            user.locked_until = now + timedelta(minutes=15)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    db.add(AuditEvent(
        actor_user_id=user.id,
        action="auth.login",
        entity_type="user",
        entity_id=str(user.id),
        details={"method": "password"},
    ))
    db.commit()
    token, expires_in = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "roles": sorted(role.name for role in user.roles),
    }


@router.get("/me")
def get_me(user: Annotated[User, Depends(get_current_user)]):
    return user_payload(user)


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: DatabaseSession,
    actor: Annotated[str | User, Depends(require_admin)],
):
    ensure_default_roles(db)
    existing = db.scalar(select(User).where(func.lower(User.email) == payload.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="A user with this email already exists.")
    role_map = {
        role.name: role
        for role in db.scalars(select(Role).where(Role.name.in_(payload.roles))).all()
    }
    if set(role_map) != set(payload.roles):
        raise HTTPException(status_code=422, detail="One or more requested roles do not exist.")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        roles=list(role_map.values()),
    )
    db.add(user)
    db.flush()
    db.add(AuditEvent(
        actor_user_id=actor.id if isinstance(actor, User) else None,
        action="user.created",
        entity_type="user",
        entity_id=str(user.id),
        details={"email": user.email, "roles": payload.roles},
    ))
    db.commit()
    db.refresh(user)
    return user_payload(user)


@router.get("/users")
def list_users(
    db: DatabaseSession,
    _actor: Annotated[str | User, Depends(require_admin)],
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    users = db.scalars(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return [user_payload(user) for user in users]


@router.patch("/users/{user_id}/roles")
def update_user_roles(
    user_id: int,
    payload: RolesUpdate,
    db: DatabaseSession,
    actor: Annotated[str | User, Depends(require_admin)],
):
    ensure_default_roles(db)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    roles = db.scalars(select(Role).where(Role.name.in_(payload.roles))).all()
    role_map = {role.name: role for role in roles}
    if set(role_map) != set(payload.roles):
        raise HTTPException(status_code=422, detail="One or more requested roles do not exist.")
    user.roles = list(role_map.values())
    db.add(AuditEvent(
        actor_user_id=actor.id if isinstance(actor, User) else None,
        action="user.roles_updated",
        entity_type="user",
        entity_id=str(user.id),
        details={"roles": payload.roles},
    ))
    db.commit()
    db.refresh(user)
    return user_payload(user)


@router.patch("/users/{user_id}/active")
def update_user_active(
    user_id: int,
    payload: ActiveUpdate,
    db: DatabaseSession,
    actor: Annotated[str | User, Depends(require_admin)],
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = payload.is_active
    db.add(AuditEvent(
        actor_user_id=actor.id if isinstance(actor, User) else None,
        action="user.active_updated",
        entity_type="user",
        entity_id=str(user.id),
        details={"is_active": user.is_active},
    ))
    db.commit()
    return user_payload(user)
