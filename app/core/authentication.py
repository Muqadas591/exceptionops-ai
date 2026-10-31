from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User


password_hasher = PasswordHash.recommended()

bearer_scheme = HTTPBearer(auto_error=False)

JWT_ALGORITHM = "HS256"


def _get_secret_key() -> str:
    """
    Fail closed when the JWT secret is missing or too short.
    """
    secret = get_settings().auth_secret_key

    if len(secret) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured correctly.",
        )

    return secret


def hash_password(password: str) -> str:
    """Return an Argon2 password hash."""
    return password_hasher.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    """Verify a password without storing or comparing plaintext."""
    try:
        return password_hasher.verify(
            password,
            password_hash,
        )
    except Exception:
        return False


def create_access_token(user: User) -> str:
    """Create a short-lived signed access token."""
    settings = get_settings()

    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        _get_secret_key(),
        algorithm=JWT_ALGORITHM,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the bearer token and load the current active user.

    The user's role is read from the database, rather than trusted
    from a role claim supplied by the client.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            _get_secret_key(),
            algorithms=[JWT_ALGORITHM],
            options={
                "require": ["sub", "iat", "exp"],
            },
        )

        subject = payload.get("sub")

        if not isinstance(subject, str):
            raise jwt.InvalidTokenError(
                "Invalid subject."
            )

        user_id = int(subject)

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is unavailable.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_roles(*allowed_roles: str):
    """
    Build a FastAPI dependency that checks database-backed roles.
    """
    def role_dependency(
        user: User = Depends(get_current_user),
    ) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return user

    return role_dependency