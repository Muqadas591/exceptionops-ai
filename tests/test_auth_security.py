
import jwt

from sqlalchemy.orm import Session

from app.core.authentication import (
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    JWT_ISSUER,
    hash_password,
)

from app.core.config import get_settings

from app.models.user import User


TEST_SECRET = (
    "Test-Auth-Security-Secret-7F2!xQ9@vM4#kR8$wP6^"
)

TEST_PASSWORD = "Synthetic-Test-Password-123!"


def configure_test_secret(monkeypatch):
    monkeypatch.setattr(
        get_settings(),
        "auth_secret_key",
        TEST_SECRET,
    )


def create_test_user(
    test_engine,
    email="security@example.com",
):
    with Session(test_engine) as db:
        db.add(
            User(
                email=email,
                password_hash=hash_password(TEST_PASSWORD),
                role="reviewer",
                is_active=True,
            )
        )

        db.commit()


def login(
    client,
    test_engine,
    monkeypatch,
):
    configure_test_secret(monkeypatch)

    create_test_user(test_engine)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "security@example.com",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    return response.json()


def test_access_token_contains_security_claims(
    unauthenticated_client,
    test_engine,
    monkeypatch,
):
    result = login(
        unauthenticated_client,
        test_engine,
        monkeypatch,
    )

    token = result["access_token"]

    claims = jwt.decode(
        token,
        TEST_SECRET,
        algorithms=[JWT_ALGORITHM],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
    )

    assert claims["iss"] == JWT_ISSUER
    assert claims["aud"] == JWT_AUDIENCE
    assert claims["token_use"] == "access"

    assert claims["sub"].isdigit()
    assert claims["jti"]

    # Roles are deliberately not embedded in the JWT.
    assert "role" not in claims

    # Password hashes must never appear in the login response.
    assert "password_hash" not in result["user"]


def test_access_token_rejects_wrong_audience(
    unauthenticated_client,
    test_engine,
    monkeypatch,
):
    result = login(
        unauthenticated_client,
        test_engine,
        monkeypatch,
    )

    token = result["access_token"]

    claims = jwt.decode(
        token,
        TEST_SECRET,
        algorithms=[JWT_ALGORITHM],
        options={
            "verify_aud": False,
        },
    )

    claims["aud"] = "another-service"

    wrong_audience_token = jwt.encode(
        claims,
        TEST_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    response = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": (
                f"Bearer {wrong_audience_token}"
            ),
        },
    )

    assert response.status_code == 401


def test_access_token_rejects_wrong_token_purpose(
    unauthenticated_client,
    test_engine,
    monkeypatch,
):
    result = login(
        unauthenticated_client,
        test_engine,
        monkeypatch,
    )

    token = result["access_token"]

    claims = jwt.decode(
        token,
        TEST_SECRET,
        algorithms=[JWT_ALGORITHM],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
    )

    claims["token_use"] = "refresh"

    wrong_purpose_token = jwt.encode(
        claims,
        TEST_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    response = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": (
                f"Bearer {wrong_purpose_token}"
            ),
        },
    )

    assert response.status_code == 401


def test_tampered_access_token_is_rejected(
    unauthenticated_client,
    test_engine,
    monkeypatch,
):
    result = login(
        unauthenticated_client,
        test_engine,
        monkeypatch,
    )

    token = result["access_token"]

    tampered_token = (
        token[:-1]
        + ("A" if token[-1] != "A" else "B")
    )

    response = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {tampered_token}",
        },
    )

    assert response.status_code == 401
