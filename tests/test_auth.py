
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.authentication import hash_password
from app.core.config import get_settings
from app.models.user import User

import jwt
from datetime import datetime, timedelta, timezone

from app.core.authentication import JWT_ALGORITHM


TEST_SECRET = "test-auth-secret-that-is-long-enough"
TEST_PASSWORD = "test-password"


def set_test_auth_secret(monkeypatch):
    monkeypatch.setattr(
        get_settings(),
        "auth_secret_key",
        TEST_SECRET,
    )


def create_user(
    test_engine,
    *,
    email: str,
    role: str,
    is_active: bool = True,
) -> None:
    with Session(test_engine) as db:
        db.add(
            User(
                email=email,
                password_hash=hash_password(TEST_PASSWORD),
                role=role,
                is_active=is_active,
            )
        )
        db.commit()


def login_and_get_token(
    client,
    test_engine,
    monkeypatch,
    *,
    email: str,
    role: str,
) -> str:
    set_test_auth_secret(monkeypatch)

    create_user(
        test_engine,
        email=email,
        role=role,
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def bearer_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
    }


def test_login_returns_access_token_for_active_user(
    unauthenticated_client,
    test_engine,
    monkeypatch,
):
    token = login_and_get_token(
        unauthenticated_client,
        test_engine,
        monkeypatch,
        email="reviewer@example.com",
        role="reviewer",
    )

    current_user = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers=bearer_headers(token),
    )

    assert current_user.status_code == 200
    assert current_user.json()["email"] == "reviewer@example.com"
    assert current_user.json()["role"] == "reviewer"


def test_login_rejects_inactive_user(
    unauthenticated_client,
    test_engine,
    monkeypatch,
):
    set_test_auth_secret(monkeypatch)

    create_user(
        test_engine,
        email="inactive@example.com",
        role="reviewer",
        is_active=False,
    )

    response = unauthenticated_client.post(
        "/api/v1/auth/login",
        json={
            "email": "inactive@example.com",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/v1/reviews/queue",
        "/api/v1/actions/recovery/queue",
        "/api/v1/audit/events",
    ],
)
def test_protected_endpoints_reject_missing_token(
    unauthenticated_client,
    endpoint,
):
    response = unauthenticated_client.get(endpoint)

    assert response.status_code == 401


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/v1/reviews/queue",
        "/api/v1/actions/recovery/queue",
        "/api/v1/audit/events",
    ],
)
def test_protected_endpoints_reject_invalid_token(
    unauthenticated_client,
    test_engine,
    monkeypatch,
    endpoint,
):
    set_test_auth_secret(monkeypatch)

    response = unauthenticated_client.get(
        endpoint,
        headers=bearer_headers("invalid.token.value"),
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("role", "endpoint", "expected_status"),
    [
        # Admin can access all three protected areas.
        ("admin", "/api/v1/reviews/queue", 200),
        ("admin", "/api/v1/actions/recovery/queue", 200),
        ("admin", "/api/v1/audit/events", 200),

        # Reviewer can access review operations only.
        ("reviewer", "/api/v1/reviews/queue", 200),
        ("reviewer", "/api/v1/actions/recovery/queue", 403),
        ("reviewer", "/api/v1/audit/events", 403),

        # Action operator can access action and audit operations.
        ("action_operator", "/api/v1/reviews/queue", 403),
        ("action_operator", "/api/v1/actions/recovery/queue", 200),
        ("action_operator", "/api/v1/audit/events", 200),
    ],
)
def test_role_permission_matrix(
    unauthenticated_client,
    test_engine,
    monkeypatch,
    role,
    endpoint,
    expected_status,
):
    email = f"{role}@example.com"

    token = login_and_get_token(
        unauthenticated_client,
        test_engine,
        monkeypatch,
        email=email,
        role=role,
    )

    response = unauthenticated_client.get(
        endpoint,
        headers=bearer_headers(token),
    )

    assert response.status_code == expected_status


def test_deactivated_user_cannot_use_previously_issued_token(
    unauthenticated_client,
    test_engine,
    monkeypatch,
):
    token = login_and_get_token(
        unauthenticated_client,
        test_engine,
        monkeypatch,
        email="deactivated@example.com",
        role="reviewer",
    )

    with Session(test_engine) as db:
        user = (
            db.query(User)
            .filter(User.email == "deactivated@example.com")
            .one()
        )
        user.is_active = False
        db.commit()

    response = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers=bearer_headers(token),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "User is unavailable."

def test_expired_token_is_rejected(
    unauthenticated_client,
    test_engine,
    monkeypatch,
):
    set_test_auth_secret(monkeypatch)

    create_user(
        test_engine,
        email="expired@example.com",
        role="reviewer",
    )

    with Session(test_engine) as db:
        user = (
            db.query(User)
            .filter(User.email == "expired@example.com")
            .one()
        )
        user_id = user.id

    now = datetime.now(timezone.utc)

    expired_token = jwt.encode(
        {
            "sub": str(user_id),
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        },
        TEST_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    response = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers=bearer_headers(expired_token),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid or expired access token."
    )
