from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.authentication import (
    create_access_token,
    get_current_user,
    verify_password,
)
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserRead,
)


router = APIRouter(tags=["Authentication"])


@router.post(
    "/auth/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate a user and return a short-lived access token.
    """
    email = str(request.email).strip().lower()

    user = db.scalar(
        select(User).where(
            func.lower(User.email) == email
        )
    )

    # Return the same error for an unknown account and an incorrect
    # password so the endpoint does not reveal whether an account exists.
    if (
        user is None
        or not user.is_active
        or not verify_password(
            request.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=(
            get_settings().access_token_expire_minutes * 60
        ),
        user=UserRead.model_validate(user),
    )


@router.get(
    "/auth/me",
    response_model=UserRead,
)
def read_current_user(
    user: User = Depends(get_current_user),
) -> User:
    """Return the identity and role associated with the current token."""
    return user