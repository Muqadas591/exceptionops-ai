
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401 - register models
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
import app.services.document_ingestion as ingestion_service


@pytest.fixture
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def document_storage(tmp_path, monkeypatch):
    settings = get_settings()

    monkeypatch.setattr(
        settings,
        "document_storage_dir",
        str(tmp_path),
    )
    monkeypatch.setattr(
        ingestion_service,
        "get_settings",
        lambda: settings,
    )

    return tmp_path


@pytest.fixture
def client(test_engine, document_storage):
    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
