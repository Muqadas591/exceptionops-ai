
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.audit_event import AuditEvent
from app.models.document import Document
import app.services.retention_service as retention_service


def upload_test_document(
    client,
    content=b"Synthetic retention test invoice",
):
    response = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "retention-invoice.txt",
                content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 201
    return response.json()


def test_retention_summary_reports_document_and_audit_counts(
    client,
):
    upload_test_document(client)

    response = client.get("/api/v1/retention/summary")

    assert response.status_code == 200

    body = response.json()

    assert body["total_documents"] == 1
    assert body["available_document_content"] == 1
    assert body["deletion_pending"] == 0
    assert body["deleted_document_content"] == 0

    assert body["audit_event_count"] >= 1
    assert body["document_content_auto_delete_enabled"] is False
    assert body["audit_event_auto_delete_enabled"] is False


def test_retention_preview_does_not_delete_documents(
    client,
    document_storage,
    test_engine,
):
    uploaded = upload_test_document(client)

    with Session(test_engine) as db:
        document = db.get(Document, uploaded["id"])
        document.created_at = (
            datetime.now(timezone.utc) - timedelta(days=30)
        )
        db.commit()

    response = client.get(
        "/api/v1/retention/documents/eligible",
        params={"older_than_days": 7},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == uploaded["id"]

    # Preview must not remove the original file.
    assert len(list(document_storage.iterdir())) == 1

    with Session(test_engine) as db:
        document = db.get(Document, uploaded["id"])
        assert document.content_status == "available"


def test_retention_preview_requires_a_configured_or_explicit_age(
    client,
    monkeypatch,
):
    settings = get_settings()

    monkeypatch.setattr(
        settings,
        "document_content_retention_days",
        0,
    )

    response = client.get(
        "/api/v1/retention/documents/eligible"
    )

    assert response.status_code == 400


def test_admin_purge_deletes_file_but_preserves_document_metadata(
    client,
    document_storage,
    test_engine,
):
    uploaded = upload_test_document(client)
    document_id = uploaded["id"]

    stored_files = list(document_storage.iterdir())

    assert len(stored_files) == 1

    stored_file = stored_files[0]
    assert stored_file.is_file()

    response = client.post(
        f"/api/v1/retention/documents/{document_id}/purge",
        json={
            "reason": "Synthetic test retention cleanup",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["document_id"] == document_id
    assert body["content_status"] == "deleted"
    assert body["content_deleted_at"] is not None

    assert not stored_file.exists()

    # The document database row is preserved.
    metadata_response = client.get(
        f"/api/v1/documents/{document_id}"
    )

    assert metadata_response.status_code == 200

    metadata = metadata_response.json()

    assert metadata["id"] == document_id
    assert metadata["original_filename"] == "retention-invoice.txt"
    assert metadata["content_status"] == "deleted"
    assert metadata["checksum_sha256"] == uploaded["checksum_sha256"]

    # The document remains in the document listing.
    listing = client.get("/api/v1/documents")

    assert listing.status_code == 200
    assert any(
        item["id"] == document_id
        for item in listing.json()
    )

    # The content endpoint must report that the content is gone.
    download = client.get(
        f"/api/v1/documents/{document_id}/content"
    )

    assert download.status_code == 410

    # Both lifecycle events remain in the audit trail.
    with Session(test_engine) as db:
        events = (
            db.query(AuditEvent)
            .filter(AuditEvent.document_id == document_id)
            .all()
        )

        event_types = {
            event.event_type
            for event in events
        }

        assert "document.uploaded" in event_types
        assert "document.content_deletion_requested" in event_types
        assert "document.content_purged" in event_types


def test_repeated_purge_is_idempotent(
    client,
    test_engine,
):
    uploaded = upload_test_document(client)
    document_id = uploaded["id"]

    payload = {
        "reason": "Synthetic test retention cleanup",
    }

    first = client.post(
        f"/api/v1/retention/documents/{document_id}/purge",
        json=payload,
    )

    assert first.status_code == 200

    with Session(test_engine) as db:
        count_before = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.document_id == document_id,
                AuditEvent.event_type == "document.content_purged",
            )
            .count()
        )

    second = client.post(
        f"/api/v1/retention/documents/{document_id}/purge",
        json=payload,
    )

    assert second.status_code == 200
    assert second.json()["content_status"] == "deleted"

    with Session(test_engine) as db:
        count_after = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.document_id == document_id,
                AuditEvent.event_type == "document.content_purged",
            )
            .count()
        )

    assert count_before == 1
    assert count_after == 1


def test_failed_file_deletion_remains_pending_and_can_be_retried(
    client,
    document_storage,
    test_engine,
):
    uploaded = upload_test_document(client)
    document_id = uploaded["id"]

    original_delete = retention_service.delete_stored_file

    def fail_delete(storage_key, settings):
        raise OSError("Synthetic filesystem failure")

    retention_service.delete_stored_file = fail_delete

    try:
        failed_response = client.post(
            f"/api/v1/retention/documents/{document_id}/purge",
            json={
                "reason": "Synthetic test retention cleanup",
            },
        )
    finally:
        retention_service.delete_stored_file = original_delete

    assert failed_response.status_code == 503

    with Session(test_engine) as db:
        document = db.get(Document, document_id)
        assert document.content_status == "deletion_pending"

    # Retry with the real filesystem deletion function.
    retry_response = client.post(
        f"/api/v1/retention/documents/{document_id}/purge",
        json={
            "reason": "Synthetic test retention cleanup",
        },
    )

    assert retry_response.status_code == 200
    assert retry_response.json()["content_status"] == "deleted"

    assert list(document_storage.iterdir()) == []


def test_missing_document_purge_returns_404(client):
    response = client.post(
        "/api/v1/retention/documents/999999/purge",
        json={
            "reason": "Synthetic test retention cleanup",
        },
    )

    assert response.status_code == 404


def test_retention_endpoints_require_authentication(
    unauthenticated_client,
):
    response = unauthenticated_client.get(
        "/api/v1/retention/summary"
    )

    assert response.status_code == 401
