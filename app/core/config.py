
from functools import lru_cache
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def is_absolute_storage_path(value: str) -> bool:
    """Accept absolute paths for both Windows and Linux."""
    path = str(value).strip()

    if not path:
        return False

    return (
        PurePosixPath(path).is_absolute()
        or PureWindowsPath(path).is_absolute()
    )


def is_valid_production_secret(secret: str) -> bool:
    """
    Check that a production secret is configured and is not an
    obvious placeholder or a low-diversity repeated value.

    This is a configuration sanity check, not an entropy measurement.
    """
    if not secret or len(secret) < 32:
        return False

    if len(set(secret)) < 8:
        return False

    lowered = secret.strip().lower()

    placeholders = (
        "replace_with_",
        "change_me",
        "changeme",
        "your_secret",
        "your-secret",
        "password",
    )

    if any(marker in lowered for marker in placeholders):
        return False

    if secret != secret.strip():
        return False

    return True


def is_valid_production_origin(origin: str) -> bool:
    """Validate an individual production CORS origin."""
    if not origin or "*" in origin:
        return False

    try:
        parsed = urlsplit(origin)
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    if not parsed.hostname:
        return False

    if parsed.username or parsed.password:
        return False

    # An origin must not contain a path, query, or fragment.
    if parsed.path not in {"", "/"}:
        return False

    if parsed.query or parsed.fragment:
        return False

    # Non-local production origins must use HTTPS.
    local_hosts = {
        "localhost",
        "127.0.0.1",
        "::1",
    }

    if (
        parsed.scheme == "http"
        and parsed.hostname.lower() not in local_hosts
    ):
        return False

    return True


class Settings(BaseSettings):
    # Application.
    app_name: str = "ExceptionOps AI"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database.
    database_url: str = (
        "postgresql+psycopg://exceptionops:"
        "change_me_local_only@localhost:5432/exceptionops"
    )

    database_pool_size: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    database_max_overflow: int = Field(
        default=5,
        ge=0,
        le=30,
    )

    database_pool_timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=120,
    )

    database_pool_recycle_seconds: int = Field(
        default=1800,
        ge=60,
    )

    # Document ingestion and storage.
    max_upload_size_bytes: int = Field(
        default=10 * 1024 * 1024,
        ge=1024,
        le=100 * 1024 * 1024,
    )

    document_storage_dir: str = ".local_storage/documents"

    # Retention policies.
    document_content_retention_days: int = Field(
        default=0,
        ge=0,
        le=36500,
    )

    audit_event_retention_days: int = Field(
        default=0,
        ge=0,
        le=36500,
    )

    # Authentication.
    auth_secret_key: str = ""

    access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=60,
    )

    # HTTP security.
    cors_allowed_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )

    allowed_hosts: str = (
        "localhost,127.0.0.1,testserver"
    )

    # API documentation.
    expose_api_docs: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated frontend origins."""
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @property
    def allowed_hosts_list(self) -> list[str]:
        """Parse comma-separated trusted hostnames."""
        return [
            host.strip()
            for host in self.allowed_hosts.split(",")
            if host.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() == "production"

    @property
    def docs_enabled(self) -> bool:
        """Never expose interactive API documentation in production."""
        return self.expose_api_docs and not self.is_production

    @model_validator(mode="after")
    def validate_production_settings(self):
        if not self.is_production:
            return self

        errors: list[str] = []

        if self.debug:
            errors.append(
                "DEBUG must be false in production."
            )

        if not is_valid_production_secret(
            self.auth_secret_key
        ):
            errors.append(
                "AUTH_SECRET_KEY must be a strong, non-placeholder "
                "secret with at least 32 characters and sufficient "
                "character diversity."
            )

        if (
            "change_me_local_only" in self.database_url
            or "replace_with_" in self.database_url
        ):
            errors.append(
                "DATABASE_URL still contains a placeholder password."
            )

        if self.database_url.startswith("sqlite"):
            errors.append(
                "Production must use a persistent database, "
                "not SQLite."
            )

        origins = self.cors_origins_list

        if not origins:
            errors.append(
                "CORS_ALLOWED_ORIGINS must contain a frontend origin."
            )
        elif not all(
            is_valid_production_origin(origin)
            for origin in origins
        ):
            errors.append(
                "Production CORS origins must be valid, non-wildcard "
                "origins. Non-local origins must use HTTPS."
            )

        hosts = self.allowed_hosts_list

        if not hosts:
            errors.append(
                "ALLOWED_HOSTS must not be empty."
            )

        if any("*" in host for host in hosts):
            errors.append(
                "ALLOWED_HOSTS must not contain wildcard entries."
            )

        if not is_absolute_storage_path(
            self.document_storage_dir
        ):
            errors.append(
                "DOCUMENT_STORAGE_DIR must be an absolute path "
                "in production."
            )

        if errors:
            raise ValueError(
                "Invalid production configuration: "
                + " ".join(errors)
            )

        return self


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
