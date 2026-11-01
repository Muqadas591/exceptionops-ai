from sqlalchemy.orm import Session

from app.core.authentication import hash_password
from app.core.config import get_settings
from app.models.user import User


def test_login_returns_access_token_for_active_user(
    client,
    test_engine,
    monkeypatch,
):
    monkeypatch.setattr(
        get_settings(),
        "auth_secret_key",
        "test-auth-secret-that-is-long-enough",
    )

    email = "reviewer@example.com"
    password = "test-password"

    with Session(test_engine) as db:
        db.add(
            User(
                email=email,
                password_hash=hash_password(password),
                role="reviewer",
                is_active=True,
            )
        )
        db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200
    access_token = response.json()["access_token"]

    current_user = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert current_user.status_code == 200
    assert current_user.json()["email"] == email
