
from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.business_evaluation import BusinessEvaluation
from app.models.document import Document
from app.models.extraction_result import ExtractionResult
from app.services.business_rules import (
    _field_value,
    evaluate_invoice_fields,
)


def _normalize(value: Any) -> str:
    if value is None:
        return ""

    return " ".join(str(value).strip().casefold().split())


def _is_duplicate(
    db: Session,
    *,
    current_document_id: int,
    current_fields: dict[str, Any],
) -> bool:
    """
    Find a possible duplicate in previously extracted documents.

    A match requires both a non-empty invoice number and a
    non-empty supplier name. Exact file checksum deduplication
    is already handled by Phase 2.
    """
    current_invoice_number = _normalize(
        _field_value(current_fields, "invoice_number")
    )
    current_supplier = _normalize(
        _field_value(current_fields, "supplier_name")
    )

    if not current_invoice_number or not current_supplier:
        return False

    previous_results = (
        db.query(ExtractionResult)
        .filter(ExtractionResult.document_id != current_document_id)
        .all()
    )

    for result in previous_results:
        previous_fields = result.fields or {}

        previous_invoice_number = _normalize(
            _field_value(previous_fields, "invoice_number")
        )
        previous_supplier = _normalize(
            _field_value(previous_fields, "supplier_name")
        )

        if (
            previous_invoice_number == current_invoice_number
            and previous_supplier == current_supplier
        ):
            return True

    return False


def evaluate_document(
    db: Session,
    document_id: int,
) -> BusinessEvaluation:
    """
    Evaluate the most recent Phase 3 extraction for a document.

    Re-running the evaluation updates the same evaluation record
    rather than creating duplicate rows.
    """
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    extraction = (
        db.query(ExtractionResult)
        .filter(ExtractionResult.document_id == document_id)
        .first()
    )

    if extraction is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "This document has not been extracted yet. "
                "Run the Phase 3 extraction endpoint first."
            ),
        )

    fields = extraction.fields or {}

    duplicate_detected = _is_duplicate(
        db,
        current_document_id=document_id,
        current_fields=fields,
    )

    result = evaluate_invoice_fields(
        fields,
        duplicate_detected=duplicate_detected,
    )

    evaluation = (
        db.query(BusinessEvaluation)
        .filter(BusinessEvaluation.document_id == document_id)
        .first()
    )

    if evaluation is None:
        evaluation = BusinessEvaluation(
            document_id=document_id,
            decision=result["decision"],
            risk_score=result["risk_score"],
            rules_version=result["rules_version"],
            findings=result["findings"],
            summary=result["summary"],
        )
        db.add(evaluation)
    else:
        evaluation.decision = result["decision"]
        evaluation.risk_score = result["risk_score"]
        evaluation.rules_version = result["rules_version"]
        evaluation.findings = result["findings"]
        evaluation.summary = result["summary"]

    try:
        db.commit()
        db.refresh(evaluation)
    except Exception:
        db.rollback()
        raise

    return evaluation


def get_document_evaluation(
    db: Session,
    document_id: int,
) -> BusinessEvaluation:
    evaluation = (
        db.query(BusinessEvaluation)
        .filter(BusinessEvaluation.document_id == document_id)
        .first()
    )

    if evaluation is None:
        raise HTTPException(
            status_code=404,
            detail="No business evaluation exists for this document.",
        )

    return evaluation
