
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.services.document_storage import (
    StoredFile,
    resolve_storage_path,
    save_upload,
)
from fastapi import UploadFile


class DuplicateDocumentError(Exception):
    def __init__(self, document_id: int):
        self.document_id = document_id
        super().__init__(
            f"Identical document content already exists as document "
            f"{document_id}."
        )


async def ingest_document(
    db: Session,
    upload: UploadFile,
) -> Document:
    """Store a validated file and persist its metadata."""
    settings = get_settings()
    stored: StoredFile | None = None

    try:
        stored = await save_upload(upload, settings)

        existing = db.scalar(
            select(Document).where(
                Document.checksum_sha256 == stored.checksum_sha256
            )
        )

        if existing is not None:
            duplicate_path = resolve_storage_path(
                stored.storage_key,
                settings,
            )
            duplicate_path.unlink(missing_ok=True)
            raise DuplicateDocumentError(existing.id)

        document = Document(
            original_filename=stored.original_filename,
            storage_key=stored.storage_key,
            extension=stored.extension,
            content_type=stored.content_type,
            file_size_bytes=stored.file_size_bytes,
            checksum_sha256=stored.checksum_sha256,
            status="received",
        )

        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    except IntegrityError as exc:
        # A concurrent request may have inserted the same checksum.
        db.rollback()

        if stored is not None:
            path = resolve_storage_path(stored.storage_key, settings)
            path.unlink(missing_ok=True)

            existing = db.scalar(
                select(Document).where(
                    Document.checksum_sha256 == stored.checksum_sha256
                )
            )
            if existing is not None:
                raise DuplicateDocumentError(existing.id) from exc

        raise
    except Exception:
        db.rollback()

        if stored is not None:
            path = resolve_storage_path(stored.storage_key, settings)
            path.unlink(missing_ok=True)

        raise


def get_document_file_path(document: Document) -> Path:
    """Return the safe path to a document's stored content."""
    return resolve_storage_path(
        document.storage_key,
        get_settings(),
    )
