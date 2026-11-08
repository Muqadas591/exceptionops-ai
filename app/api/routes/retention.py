
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.core.authorization import require_admin
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.retention import (
    DocumentRetentionCandidateRead,
    PurgeDocumentRequest,
    PurgeDocumentResponse,
    RetentionSummaryRead,
)
from app.services.document_storage import DocumentValidationError
from app.services.retention_service import (
    DocumentContentDeletionError,
    DocumentNotFoundError,
    get_eligible_documents,
    get_retention_summary,
    purge_document_content,
)


router = APIRouter(
    prefix="/retention",
    tags=["Data Retention"],
)


@router.get(
    "/summary",
    response_model=RetentionSummaryRead,
)
def read_retention_summary(
    db: Session = Depends(get_db),
    actor: str = Depends(require_admin),
):
    """Return document lifecycle and audit-retention statistics."""
    return get_retention_summary(db)


@router.get(
    "/documents/eligible",
    response_model=list[DocumentRetentionCandidateRead],
)
def read_eligible_documents(
    older_than_days: int | None = Query(
        default=None,
        ge=1,
        le=36500,
    ),
    db: Session = Depends(get_db),
    actor: str = Depends(require_admin),
):
    """
    Preview documents eligible for content-retention review.

    This endpoint never deletes anything.
    """
    settings = get_settings()

    effective_days = (
        older_than_days
        if older_than_days is not None
        else settings.document_content_retention_days
    )

    if effective_days < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Age-based document retention is not configured. "
                "Set DOCUMENT_CONTENT_RETENTION_DAYS or provide "
                "older_than_days explicitly."
            ),
        )

    return get_eligible_documents(
        db,
        older_than_days=effective_days,
    )


@router.post(
    "/documents/{document_id}/purge",
    response_model=PurgeDocumentResponse,
)
def purge_document(
    document_id: int,
    payload: PurgeDocumentRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(require_admin),
):
    """
    Permanently delete local file content.

    The document database row and all related business history remain.
    """
    try:
        document = purge_document_content(
            db,
            document_id=document_id,
            actor=actor,
            reason=payload.reason.strip(),
        )

    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except DocumentContentDeletionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except DocumentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if document.content_status == "deleted":
        message = (
            "Document content is deleted. "
            "Metadata and business history have been preserved."
        )
    else:
        message = "Document content deletion is pending."

    return PurgeDocumentResponse(
        document_id=document.id,
        content_status=document.content_status,
        content_deleted_at=document.content_deleted_at,
        message=message,
    )
