
import pytest

from pydantic import ValidationError

from app.core.config import Settings


PRODUCTION_SECRET = (
    "Test-Production-Secret-7F2!xQ9@vM4#kR8$wP6^"
)

PRODUCTION_DATABASE_URL = (
    "postgresql+psycopg://user:password@db.example.com/app"
)


def production_settings(**overrides):
    values = {
        "app_env": "production",
        "debug": False,
        "auth_secret_key": PRODUCTION_SECRET,
        "database_url": PRODUCTION_DATABASE_URL,
        "cors_allowed_origins": "https://app.example.com",
        "allowed_hosts": "api.example.com",
        "document_storage_dir": (
            "/var/data/exceptionops/documents"
        ),
    }

    values.update(overrides)

    return Settings(
        _env_file=None,
        **values,
    )


def test_settings_accept_explicit_values():
    settings = Settings(
        _env_file=None,
        app_name="Test ExceptionOps",
        app_env="test",
        debug=False,
        api_v1_prefix="/api/v1",
        database_url="sqlite://",
    )

    assert settings.app_name == "Test ExceptionOps"
    assert settings.app_env == "test"
    assert settings.debug is False
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.database_url == "sqlite://"


def test_cors_origins_are_parsed():
    settings = Settings(
        _env_file=None,
        cors_allowed_origins=(
            "http://localhost:5173, "
            "http://127.0.0.1:5173/"
        ),
    )

    assert settings.cors_origins_list == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_allowed_hosts_are_parsed():
    settings = Settings(
        _env_file=None,
        allowed_hosts="localhost, api.example.com",
    )

    assert settings.allowed_hosts_list == [
        "localhost",
        "api.example.com",
    ]


def test_docs_are_enabled_in_development():
    settings = Settings(
        _env_file=None,
        app_env="development",
        expose_api_docs=True,
    )

    assert settings.docs_enabled is True


def test_docs_are_disabled_in_production():
    settings = production_settings(
        expose_api_docs=True,
    )

    assert settings.docs_enabled is False


def test_production_rejects_weak_auth_secret():
    with pytest.raises(ValidationError):
        production_settings(
            auth_secret_key="short",
        )


def test_production_rejects_placeholder_auth_secret():
    with pytest.raises(ValidationError):
        production_settings(
            auth_secret_key=(
                "replace_with_a_random_secret_of_at_least_32_characters"
            ),
        )


def test_production_rejects_low_diversity_secret():
    with pytest.raises(ValidationError):
        production_settings(
            auth_secret_key="a" * 64,
        )


def test_production_rejects_placeholder_database_password():
    with pytest.raises(ValidationError):
        production_settings(
            database_url=(
                "postgresql+psycopg://user:replace_with_a_password"
                "@db.example.com/app"
            ),
        )


def test_production_rejects_debug_mode():
    with pytest.raises(ValidationError):
        production_settings(
            debug=True,
        )


def test_production_rejects_sqlite():
    with pytest.raises(ValidationError):
        production_settings(
            database_url="sqlite:///production.db",
        )


def test_production_rejects_wildcard_hosts():
    with pytest.raises(ValidationError):
        production_settings(
            allowed_hosts="*",
        )


def test_production_rejects_relative_storage_path():
    with pytest.raises(ValidationError):
        production_settings(
            document_storage_dir=".local_storage/documents",
        )


def test_production_rejects_wildcard_cors():
    with pytest.raises(ValidationError):
        production_settings(
            cors_allowed_origins="*",
        )


def test_production_rejects_insecure_remote_cors_origin():
    with pytest.raises(ValidationError):
        production_settings(
            cors_allowed_origins="http://app.example.com",
        )


def test_production_accepts_local_http_origin():
    settings = production_settings(
        cors_allowed_origins="http://localhost:5173",
    )

    assert settings.cors_origins_list == [
        "http://localhost:5173",
    ]


def test_production_rejects_cors_path():
    with pytest.raises(ValidationError):
        production_settings(
            cors_allowed_origins=(
                "https://app.example.com/dashboard"
            ),
        )


def test_production_rejects_wildcard_host_subdomain():
    with pytest.raises(ValidationError):
        production_settings(
            allowed_hosts="*.example.com",
        )
