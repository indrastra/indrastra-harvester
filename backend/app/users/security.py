import os
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from backend.app.users.models import User

password_hasher = PasswordHasher()
TOKEN_ISSUER = "indrastra-harvester"


def jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY") or os.getenv("APP_SECRET_KEY", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET_KEY or APP_SECRET_KEY must contain at least 32 characters.")
    return secret


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_access_token(user: User) -> tuple[str, int]:
    expires_in = max(5, int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))) * 60
    now = datetime.now(UTC)
    payload = {
        "iss": TOKEN_ISSUER,
        "sub": str(user.id),
        "roles": [role.name for role in user.roles],
        "is_superuser": user.is_superuser,
        "token_type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, jwt_secret(), algorithm="HS256")
    return token, expires_in


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        jwt_secret(),
        algorithms=["HS256"],
        issuer=TOKEN_ISSUER,
        options={"require": ["exp", "iat", "iss", "sub", "token_type"]},
    )
