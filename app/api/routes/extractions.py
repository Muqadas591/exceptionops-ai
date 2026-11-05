
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.extraction_result import ExtractionResult
from app.schemas.extraction import ExtractionResultRead
from app.services.invoice_extraction import extract_invoice_document
from app.core.authorization import require_reviewer

router = APIRouter(
    prefix="/documents",
    tags=["Invoice Extraction"],
    dependencies=[Depends(require_reviewer)],
)


@router.post(
    "/{document_id}/extract",
    response_model=ExtractionResultRead,
)
def run_extraction(
    document_id: int,
    db: Session = Depends(get_db),
    actor: str = Depends(require_reviewer),
) -> ExtractionResult:
    return extract_invoice_document(
        db,
        document_id,
        actor=actor,
    )


@router.get(
    "/{document_id}/extraction",
    response_model=ExtractionResultRead,
)
def get_extraction(
    document_id: int,
    db: Session = Depends(get_db),
) -> ExtractionResult:
    result = db.scalar(
        select(ExtractionResult).where(
            ExtractionResult.document_id == document_id
        )
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No extraction result exists for this document.",
        )

    return result
