
import asyncio
from pathlib import Path

import pytest
from fastapi import FastAPI

from app.core.config import get_settings
from app.core.lifespan import (
    initialize_document_storage,
    lifespan,
)


def test_initialize_document_storage_creates_directory(
    tmp_path,
    monkeypatch,
):
    settings = get_settings()
    storage_path = tmp_path / "new-storage"

    monkeypatch.setattr(
        settings,
        "document_storage_dir",
        str(storage_path),
    )

    result = initialize_document_storage()

    assert result == storage_path.resolve()
    assert storage_path.is_dir()


def test_lifespan_sets_storage_path_and_disposes_engine(
    tmp_path,
    monkeypatch,
):
    from app.core import lifespan as lifecycle_module

    settings = get_settings()
    storage_path = tmp_path / "lifecycle-storage"

    monkeypatch.setattr(
        settings,
        "document_storage_dir",
        str(storage_path),
    )

    disposed = {"value": False}

    class FakeEngine:
        def dispose(self):
            disposed["value"] = True

    monkeypatch.setattr(
        lifecycle_module,
        "engine",
        FakeEngine(),
    )

    app = FastAPI()

    async def run_lifecycle():
        async with lifespan(app):
            assert Path(app.state.document_storage_path) == (
                storage_path.resolve()
            )
            assert storage_path.is_dir()
            assert disposed["value"] is False

        assert disposed["value"] is True

    asyncio.run(run_lifecycle())


def test_lifespan_fails_when_storage_cannot_be_initialized(
    tmp_path,
    monkeypatch,
):
    settings = get_settings()

    # A regular file cannot be used as the document directory.
    storage_file = tmp_path / "storage-file"
    storage_file.write_text("blocker", encoding="utf-8")

    monkeypatch.setattr(
        settings,
        "document_storage_dir",
        str(storage_file),
    )

    app = FastAPI()

    async def run_lifecycle():
        async with lifespan(app):
            pass

    with pytest.raises(RuntimeError):
        asyncio.run(run_lifecycle())
