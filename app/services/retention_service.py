
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.audit_event import AuditEvent
from app.models.document import Document
from app.services.audit_service import record_audit_event
from app.services.document_storage import (
    DocumentValidationError,
    resolve_storage_path,
)


class DocumentNotFoundError(Exception):
    """The requested document does not exist."""


class DocumentContentDeletionError(Exception):
    """The stored file could not be deleted."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def delete_stored_file(
    storage_key: str,
    settings: Settings,
) -> None:
    """
    Delete one generated storage key.

    resolve_storage_path validates the key and prevents path traversal.
    A missing file is treated as already deleted, making retries safe.
    """
    path = resolve_storage_path(storage_key, settings)
    path.unlink(missing_ok=True)


def get_retention_summary(db: Session) -> dict:
    """Return document and audit retention statistics."""

    document_counts = {
        "available": 0,
        "deletion_pending": 0,
        "deleted": 0,
    }

    rows = db.execute(
        select(
            Document.content_status,
            func.count(Document.id),
        ).group_by(Document.content_status)
    ).all()

    for content_status, count in rows:
        document_counts[content_status] = int(count)

    audit_event_count = (
        db.scalar(
            select(func.count(AuditEvent.id))
        )
        or 0
    )

    oldest_audit_event_at = db.scalar(
        select(func.min(AuditEvent.created_at))
    )

    settings = get_settings()

    audit_review_candidates = 0

    if settings.audit_event_retention_days > 0:
        cutoff = utc_now() - timedelta(
            days=settings.audit_event_retention_days
        )

        audit_review_candidates = (
            db.scalar(
                select(func.count(AuditEvent.id)).where(
                    AuditEvent.created_at < cutoff
                )
            )
            or 0
        )

    return {
        "total_documents": sum(document_counts.values()),
        "available_document_content": document_counts["available"],
        "deletion_pending": document_counts["deletion_pending"],
        "deleted_document_content": document_counts["deleted"],
        "audit_event_count": int(audit_event_count),
        "oldest_audit_event_at": oldest_audit_event_at,
        "document_content_retention_days": (
            settings.document_content_retention_days
        ),
        "audit_event_retention_days": (
            settings.audit_event_retention_days
        ),
        "audit_events_older_than_review_threshold": int(
            audit_review_candidates
        ),
        "document_content_auto_delete_enabled": False,
        "audit_event_auto_delete_enabled": False,
    }


def get_eligible_documents(
    db: Session,
    *,
    older_than_days: int,
) -> list[Document]:
    """
    Preview documents whose content is older than the requested age.

    This function never deletes files or database records.
    """
    if older_than_days < 1:
        raise ValueError("older_than_days must be at least 1.")

    cutoff = utc_now() - timedelta(days=older_than_days)

    statement = (
        select(Document)
        .where(
            Document.content_status == "available",
            Document.created_at < cutoff,
        )
        .order_by(
            Document.created_at.asc(),
            Document.id.asc(),
        )
        .limit(500)
    )

    return list(db.scalars(statement).all())


def purge_document_content(
    db: Session,
    *,
    document_id: int,
    actor: str,
    reason: str,
) -> Document:
    """
    Purge local file content while preserving the database record.

    The operation has two phases:

    1. Commit deletion_pending and an audit event.
    2. Delete the local file, then commit deleted and another audit event.

    If the filesystem operation fails, deletion_pending remains committed.
    Calling this function again safely retries the deletion.
    """

    # Lock the document row while deciding whether a request is needed.
    document = db.scalar(
        select(Document)
        .where(Document.id == document_id)
        .with_for_update()
    )

    if document is None:
        raise DocumentNotFoundError(
            f"Document {document_id} was not found."
        )

    # Idempotent success: do not create duplicate purge events.
    if document.content_status == "deleted":
        return document

    # Record the deletion request once.
    if document.content_status != "deletion_pending":
        document.content_status = "deletion_pending"
        document.content_deletion_reason = reason
        document.content_deleted_by = actor

        record_audit_event(
            db,
            event_type="document.content_deletion_requested",
            entity_type="document",
            entity_id=document.id,
            description=(
                "Document content deletion was requested by an administrator."
            ),
            actor_type="user",
            actor_id=actor,
            document_id=document.id,
            metadata={
                "reason": reason,
                "filename": document.original_filename,
                "file_size_bytes": document.file_size_bytes,
            },
        )

        # Commit the pending state before touching the filesystem.
        db.commit()

    settings = get_settings()

    try:
        delete_stored_file(
            document.storage_key,
            settings,
        )
    except DocumentValidationError:
        # Never proceed if the key is invalid or resolves outside storage.
        raise
    except OSError as exc:
        # The committed pending state is intentionally preserved.
        raise DocumentContentDeletionError(
            "The document file could not be deleted. "
            "The document remains pending and can be retried."
        ) from exc

    # Re-read with a row lock before finalizing. This prevents duplicate
    # completion audit events if concurrent requests reach this stage.
    document = db.scalar(
        select(Document)
        .where(Document.id == document_id)
        .with_for_update()
    )

    if document is None:
        raise DocumentNotFoundError(
            f"Document {document_id} was not found."
        )

    if document.content_status == "deleted":
        return document

    document.content_status = "deleted"
    document.content_deleted_at = utc_now()
    document.content_deleted_by = actor

    record_audit_event(
        db,
        event_type="document.content_purged",
        entity_type="document",
        entity_id=document.id,
        description=(
            "Local document content was permanently deleted. "
            "Document metadata and business history were preserved."
        ),
        actor_type="user",
        actor_id=actor,
        document_id=document.id,
        metadata={
            "reason": document.content_deletion_reason,
            "filename": document.original_filename,
            "file_size_bytes": document.file_size_bytes,
            "content_status": "deleted",
        },
    )

    db.commit()
    db.refresh(document)

    return document
