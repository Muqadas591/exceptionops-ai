import pytest
from pydantic import ValidationError

from app.core.config import Settings


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
    settings = Settings(
        _env_file=None,
        app_env="production",
        debug=False,
        expose_api_docs=True,
        auth_secret_key="a" * 48,
        database_url=(
            "postgresql+psycopg://user:password@db.example.com/app"
        ),
        cors_allowed_origins="https://app.example.com",
        allowed_hosts="api.example.com",
        document_storage_dir="/var/data/exceptionops/documents",
    )

    assert settings.docs_enabled is False


def test_production_rejects_weak_auth_secret():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="production",
            debug=False,
            auth_secret_key="short",
            database_url=(
                "postgresql+psycopg://user:password@db.example.com/app"
            ),
            cors_allowed_origins="https://app.example.com",
            allowed_hosts="api.example.com",
            document_storage_dir="/var/data/exceptionops/documents",
        )


def test_production_rejects_debug_mode():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="production",
            debug=True,
            auth_secret_key="a" * 48,
            database_url=(
                "postgresql+psycopg://user:password@db.example.com/app"
            ),
            cors_allowed_origins="https://app.example.com",
            allowed_hosts="api.example.com",
            document_storage_dir="/var/data/exceptionops/documents",
        )


def test_production_rejects_sqlite():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="production",
            debug=False,
            auth_secret_key="a" * 48,
            database_url="sqlite:///production.db",
            cors_allowed_origins="https://app.example.com",
            allowed_hosts="api.example.com",
            document_storage_dir="/var/data/exceptionops/documents",
        )


def test_production_rejects_wildcard_hosts():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="production",
            debug=False,
            auth_secret_key="a" * 48,
            database_url=(
                "postgresql+psycopg://user:password@db.example.com/app"
            ),
            cors_allowed_origins="https://app.example.com",
            allowed_hosts="*",
            document_storage_dir="/var/data/exceptionops/documents",
        )


def test_production_rejects_relative_storage_path():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="production",
            debug=False,
            auth_secret_key="a" * 48,
            database_url=(
                "postgresql+psycopg://user:password@db.example.com/app"
            ),
            cors_allowed_origins="https://app.example.com",
            allowed_hosts="api.example.com",
            document_storage_dir=".local_storage/documents",
        )