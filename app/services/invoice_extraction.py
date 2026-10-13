
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.models.extraction_result import ExtractionResult
from app.services.extraction_providers import (
    InvoiceExtractionProvider,
    RuleBasedInvoiceProvider,
)
from app.services.text_extraction import (
    TextExtractionError,
    extract_document_text,
)


def get_extraction_provider() -> InvoiceExtractionProvider:
    """Select the free provider. Future providers plug in here."""
    return RuleBasedInvoiceProvider()


def extract_invoice_document(
    db: Session,
    document_id: int,
) -> ExtractionResult:
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    try:
        text = extract_document_text(document, get_settings())
    except TextExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    provider = get_extraction_provider()
    candidates = provider.extract(text)

    fields = {
        field_name: {
            "value": candidate.value,
            "confidence": candidate.confidence,
            "evidence": candidate.evidence,
        }
        for field_name, candidate in candidates.items()
    }

    # This status is a routing hint, not a claim that the invoice
    # is correct or approved. Business validation comes in Phase 4.
    needs_review = any(
        candidate.value is None or candidate.confidence < 0.80
        for candidate in candidates.values()
    )

    result_status = "needs_review" if needs_review else "extracted"

    result = db.scalar(
        select(ExtractionResult).where(
            ExtractionResult.document_id == document_id
        )
    )

    if result is None:
        result = ExtractionResult(
            document_id=document_id,
            provider_name=provider.name,
            status=result_status,
            fields=fields,
            extracted_text_length=len(text),
        )
        db.add(result)
    else:
        result.provider_name = provider.name
        result.status = result_status
        result.fields = fields
        result.extracted_text_length = len(text)
        result.error_message = None

    db.commit()
    db.refresh(result)
    return result
