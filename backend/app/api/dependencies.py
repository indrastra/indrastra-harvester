import hmac
import os
from typing import Annotated, Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.users.models import User
from backend.app.users.security import decode_access_token, jwt_secret

bearer_scheme = HTTPBearer(auto_error=False)
AdminCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]
DatabaseSession = Annotated[Session, Depends(get_db)]


def _unauthorized(detail: str = "A valid bearer token is required.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _user_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise _unauthorized("Invalid or expired access token.") from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthorized("User account is inactive or unavailable.")
    return user


def get_current_user(
    credentials: AdminCredentials,
    db: DatabaseSession,
) -> User:
    return _user_from_credentials(credentials, db)


def _has_role(user: User, allowed_roles: set[str]) -> bool:
    return user.is_superuser or any(role.name in allowed_roles for role in user.roles)


def require_admin(
    credentials: AdminCredentials,
    db: DatabaseSession,
) -> str | User:
    configured_token = os.getenv("ADMIN_API_TOKEN", "")
    try:
        jwt_secret()
        jwt_configured = True
    except RuntimeError:
        jwt_configured = False

    if len(configured_token) < 32 and not jwt_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Configure ADMIN_API_TOKEN or JWT_SECRET_KEY before enabling administration.",
        )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("An administrative bearer token is required.")
    if len(configured_token) >= 32 and hmac.compare_digest(
        credentials.credentials, configured_token
    ):
        return "admin"

    user = _user_from_credentials(credentials, db)
    if _has_role(user, {"admin"}):
        return user
    raise HTTPException(status_code=403, detail="Administrator role required.")


def require_roles(*allowed_roles: str) -> Callable:
    allowed = set(allowed_roles)

    def dependency(
        credentials: AdminCredentials,
        db: DatabaseSession,
    ) -> str | User:
        configured_token = os.getenv("ADMIN_API_TOKEN", "")
        if (
            len(configured_token) >= 32
            and credentials is not None
            and credentials.scheme.lower() == "bearer"
            and hmac.compare_digest(credentials.credentials, configured_token)
        ):
            return "admin"
        user = _user_from_credentials(credentials, db)
        if _has_role(user, allowed):
            return user
        raise HTTPException(status_code=403, detail="Insufficient role permissions.")

    return dependency
