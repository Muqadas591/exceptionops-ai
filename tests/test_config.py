
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
