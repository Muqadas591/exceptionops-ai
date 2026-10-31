from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ExceptionOps AI"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+psycopg://exceptionops:"
        "change_me_local_only@localhost:5432/exceptionops"
    )

    # Document ingestion.
    max_upload_size_bytes: int = 10 * 1024 * 1024
    document_storage_dir: str = ".local_storage/documents"

    # Authentication.
    auth_secret_key: str = ""
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return one cached settings instance per process."""
    return Settings()