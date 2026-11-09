
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.runtime_checks import (
    check_database,
    check_storage,
)


def test_database_check_succeeds(test_engine):
    with Session(test_engine) as db:
        assert check_database(db) is True


def test_database_check_fails_safely():
    class BrokenSession:
        def execute(self, statement):
            raise OperationalError(
                str(statement),
                {},
                Exception("database unavailable"),
            )

        def rollback(self):
            return None

    assert check_database(BrokenSession()) is False


def test_storage_check_succeeds(document_storage, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(
        settings,
        "document_storage_dir",
        str(document_storage),
    )

    assert check_storage(settings) is True

    # The health check must remove its temporary probe.
    assert list(document_storage.iterdir()) == []


def test_storage_check_fails_when_directory_is_missing(
    tmp_path,
    monkeypatch,
):
    settings = get_settings()
    missing_path = tmp_path / "does-not-exist"

    monkeypatch.setattr(
        settings,
        "document_storage_dir",
        str(missing_path),
    )

    assert check_storage(settings) is False
    assert not missing_path.exists()


def test_storage_check_fails_when_path_is_a_file(
    tmp_path,
    monkeypatch,
):
    settings = get_settings()
    file_path = tmp_path / "not-a-directory"
    file_path.write_text("not a directory", encoding="utf-8")

    monkeypatch.setattr(
        settings,
        "document_storage_dir",
        str(file_path),
    )

    assert check_storage(settings) is False
